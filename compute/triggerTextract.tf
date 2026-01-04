resource "aws_lambda_function" "triggerTextract" {
  filename         = data.archive_file.triggerTextract_code.output_path
  function_name    = var.latest_triggerTextract
  role             = data.terraform_remote_state.permissions.outputs.role_arn
  handler          = "${var.latest_triggerTextract}.lambda_handler"
  source_code_hash = data.archive_file.triggerTextract_code.output_base64sha256

  timeout = 10

  runtime = "python3.14"

  environment {
    variables = {
      DEST_BUCKET_NAME = data.terraform_remote_state.data_stores.outputs.dest_bucket
      DYNAMO_DB_TABLE = data.terraform_remote_state.data_stores.outputs.dynamo_table
      LOG_LEVEL        = "info"
    }
  }

  logging_config {
    log_format            = "JSON"
    application_log_level = "INFO"
    system_log_level      = "WARN"
  }

  tags = {
    Project = var.project_name
  }
}

resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.triggerTextract.arn
  principal     = "s3.amazonaws.com"
  source_arn  = data.terraform_remote_state.data_stores.outputs.source_bucket_arn
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = data.terraform_remote_state.data_stores.outputs.source_bucket

  lambda_function {
    lambda_function_arn = aws_lambda_function.triggerTextract.arn
    events              = ["s3:ObjectCreated:*"]
    # Optional: use filter_prefix or filter_suffix to restrict triggers to specific paths/file types
    # filter_prefix = "uploads/"
  }

  depends_on = [aws_lambda_permission.allow_bucket]

}