from email import message
from django.test import TestCase
import base64
import boto3

from .application.score_evaluation_application import ScoreEvaluationApplication
from .infrastructure.sqs_infrastructure import EvaluationMessageRepositoryInterface
from .domain.model.entity import Evaluation
from .domain.model.score_evaluation_message_pb2 import ScoreEvaluationMessage
from .usecase.score_evaluation_usecase import ScoreEvaluationUsecase

class ScoreEvaluationTests(TestCase):
    def test_default_evaluation(self):
        eval = Evaluation(
            repository_url="https://github.com/seigot/tetris",
            branch="master",
            trial_num=5,
            level=1,
            game_time=2
        )
        usecase = ScoreEvaluationApplication(eval)
        eval = usecase.evaluate()
        self.assertEqual(eval.status, "S")

    def test_error_branch(self):
        """
        with invalid branch name, git clone would be failed
        """   
        eval = Evaluation(
            repository_url="https://github.com/seigot/tetris",
            branch="masterrr",
            trial_num=1,
            level=1,
            game_time=2
        )
        usecase = ScoreEvaluationApplication(eval)
        eval = usecase.evaluate()
        self.assertEqual(eval.status, "ER")
    
    def test_error_empty_value_mode(self):
        """
        with brank value mode, tetris start cmd would be failed
        """  
        eval = Evaluation(
            repository_url="https://github.com/seigot/tetris",
            branch="master",
            game_mode = "",
            trial_num=1,
            level=1,
            game_time=2
        )
        usecase = ScoreEvaluationApplication(eval)
        eval = usecase.evaluate()
        self.assertEqual(eval.status, "ER")
    
    def test_error_time_out(self):
        """
        with brank value mode, tetris start cmd would be failed
        """  
        eval = Evaluation(
            repository_url="https://github.com/seigot/tetris",
            branch="master",
            trial_num=1,
            level=1,
            game_time=10,
            timeout=1
        )
        usecase = ScoreEvaluationApplication(eval)
        eval = usecase.evaluate()
        self.assertEqual(eval.status, "ER")
        

class InterfaceTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sqs_client = boto3.client('sqs', region_name='ap-northeast-1')
        response = cls.sqs_client.create_queue(
            QueueName='test_evaluation_message_queue'
        )
        cls.sqs_url = response["QueueUrl"]
        test_msg = ScoreEvaluationMessage()
        test_msg.repository_url = "https://github.com/seigot/tetris"
        test_msg.branch = "master"
        test_msg.drop_interval = 1000
        test_msg.level = 1
        test_msg.game_mode = "default"
        test_msg.game_time=10
        test_msg.timeout=200
        test_msg.trial_num=1
        message = str(base64.b64encode(test_msg.SerializeToString()))
        cls.message = message
        cls.msg_if = EvaluationMessageRepositoryInterface(cls.sqs_url)

    @classmethod
    def tearDownClass(cls):
        cls.sqs_client.delete_queue(
            QueueUrl=cls.sqs_url
        )
    
    def setUp(self):
        self.sqs_client.send_message(
            QueueUrl=self.sqs_url,
            MessageBody=self.message
        )

    def test_fetch_message(self):
        eval = self.msg_if.fetch_message()
        self.assertNotEqual(eval.repository_url, "")
    
    def test_delete_message(self):
        eval = self.msg_if.fetch_message()
        res = self.msg_if.delete_message(eval)
        self.assertEqual(res["ResponseMetadata"]['HTTPStatusCode'], 200)
