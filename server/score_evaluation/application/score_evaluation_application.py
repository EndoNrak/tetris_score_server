import os
import shutil
import json
from datetime import datetime
from statistics import mean, stdev
import subprocess
from concurrent.futures import ThreadPoolExecutor

from ..domain.model.entity import Evaluation

class ScoreEvaluationApplication:
    def __init__(self, evaluation: Evaluation) -> None:
        self.evaluation = evaluation

    def evaluate(self)-> Evaluation:
        log_folder = "/server/log"
        res = clone_repository(url=self.evaluation.repository_url, branch=self.evaluation.branch)
        if res.returncode:
            self.evaluation.status = "ER"
            self.evaluation.error_message = res.stderr
            self.evaluation.ended_at = str(datetime.now())
            return self.evaluation
        
        # execute tetris_start asynchronously
        futures = []
        with ThreadPoolExecutor() as pool:
            for i in range(self.evaluation.trial_num):
                future = pool.submit(
                    tetris_start, 
                    game_time=self.evaluation.game_time,
                    log_file=f"{log_folder}/result-{i}.json", 
                    level=self.evaluation.level,
                    drop_interval=self.evaluation.drop_interval,
                    game_mode=self.evaluation.game_mode,
                    value_predict_weight=self.evaluation.value_predict_weight,
                    timeout=self.evaluation.timeout
                    )
                futures.append(future)
        scores = []
        for i, future in enumerate(futures):
            with open(f"{log_folder}/result-{i}.log", 'w', encoding='utf-8') as f:
                result = future.result()
                if result.stdout is not None:
                    f.write(result.stdout)
                else:
                    f.write(result.stderr)
                if result.returncode:
                    self.evaluation.status = "ER"
                    self.evaluation.error_message = result.stdout
                    self.evaluation.ended_at = str(datetime.now())
                    return self.evaluation
            with open(f"{log_folder}/result-{i}.json", 'r', encoding='utf-8') as f:
                res = json.load(f)
                scores.append(int(res["judge_info"]["score"]))

        # calculate statics
        self.evaluation.ended_at = str(datetime.now())
        self.evaluation.score_mean = mean(scores)
        self.evaluation.score_max = max(scores)
        self.evaluation.score_min = min(scores)
        if len(scores) > 1:
            self.evaluation.score_stdev = stdev(scores)
        self.evaluation.status = "S"
        

        return self.evaluation

def clone_repository(url: str, branch: str):
    """
    clone repository in /home/tetris
    if tetris folder is already exists, git clone after removing
    """
    os.chdir("/home")
    if os.path.exists("tetris"):
        shutil.rmtree("tetris")
    git_clone_command = f"git clone {url} -b {branch} tetris --depth=1" # --depth=1: clone only head
    result = subprocess.run(git_clone_command.split(), capture_output=True, encoding='utf-8')
    return result

def tetris_start(level: int, game_time: int, drop_interval: int, game_mode: str, value_predict_weight: str, timeout: int, log_file="result.json"):
    os.chdir("/home/tetris")
    tetris_start_command = f"xvfb-run -a python start.py -l {level} -t {game_time} -d {drop_interval} -m {game_mode} -f {log_file}"
    if value_predict_weight != "":
        tetris_start_command += f" --predict_weight {value_predict_weight}"
    try:
        result = subprocess.run(
            tetris_start_command.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding='utf-8',
            timeout=timeout
        )
    except subprocess.SubprocessError as e:
        result = subprocess.CalledProcessError(
            returncode=10,
            cmd=tetris_start_command.split(),
            stderr=str(e)
        )
    return result
