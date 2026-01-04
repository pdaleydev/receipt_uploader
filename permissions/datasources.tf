data "terraform_remote_state" "data_stores" {
  backend = "local"
  config = {
    path = "../data_stores/terraform.tfstate"
  }
}

data "aws_iam_policy_document" "lambda_trust_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    effect  = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "triggerTextract_permissions_doc" {

  # 1. Read from Source Bucket
  statement {
    sid    = "AllowS3Read"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:ListBucket"
    ]
    resources = [
      "arn:aws:s3:::${data.terraform_remote_state.data_stores.outputs.source_bucket}",
      "arn:aws:s3:::${data.terraform_remote_state.data_stores.outputs.source_bucket}/*"
    ]
  }

  # 2. Interact with Textract.
  statement {
    sid       = "AllowTextractFull"
    effect    = "Allow"
    actions   = ["textract:*"]
    resources = ["*"]
  }

  # 3. Write to Destination Bucket
  statement {
    sid     = "AllowS3Write"
    effect  = "Allow"
    actions = ["s3:PutObject"]
    resources = [
      "arn:aws:s3:::${data.terraform_remote_state.data_stores.outputs.dest_bucket}/*"
    ]
  }

  # 4. Write to DynamoDB
    statement {
      sid       = "AllowDynamoDBWrite"
      effect    = "Allow"
      actions   = [
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:BatchWriteItem"
      ]
      resources = ["${data.terraform_remote_state.data_stores.outputs.dynamo_table _arn}"]
    }

  # 5. Logging
  statement {
    sid    = "AllowCloudWatchLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["arn:aws:logs:*:*:*"]
  }
}
