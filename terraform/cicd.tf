resource "aws_iam_openid_connect_provider" "github_actions" {
  url = var.github_oidc_url
  client_id_list = [
    var.oidc_sts_url,
  ]
  thumbprint_list = []
}

data "aws_caller_identity" "my_id" {}

data "aws_iam_policy_document" "oidc_assume_role" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    principals {
      type        = "Federated"
      identifiers = ["arn:aws:iam::[${data.aws_caller_identity.my_id.account_id}]:oidc-provider/token.actions.githubusercontent.com"]
    }
    condition {
      test     = "ForAnyValue:StringEquals"
      values   = ["token.actions.githubusercontent.com:sub"]
      variable = "repo:${var.github_repository}:*"
    }
  }
}

resource "aws_iam_role" "github_oidc_role" {
  name               = var.oidc_role_name
  assume_role_policy = data.aws_iam_policy_document.oidc_assume_role.json
}

resource "aws_iam_policy" "github_oidc_policy" {
  name   = var.oidc_policy_name
  policy = data.aws_iam_policy_document.message_to_sqs_policy_doc.json
}

resource "aws_iam_role_policy_attachment" "oidc_attachment" {
  role       = aws_iam_role.github_oidc_role.name
  policy_arn = var.oidc_policy_arn
}
