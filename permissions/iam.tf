resource "aws_iam_role" "lambda_role" {
  name               = "triggerTextract_lambda_role"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust_policy.json
}

resource "aws_iam_policy" "triggerTextract_policy" {
  name        = "triggerTextract_policy"
  description = "Policy for reading S3 source, writing S3 dest, and writing DynamoDB"
  policy      = data.aws_iam_policy_document.triggerTextract_permissions_doc.json
}

resource "aws_iam_role_policy_attachment" "attach_triggerTextract_policy" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.triggerTextract_policy.arn
}