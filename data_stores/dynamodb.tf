resource "aws_dynamodb_table" "receipt_table" {
  name           = var.dynamo_table_name
  billing_mode   = "PAY_PER_REQUEST"

  # Define the primary hash key
  hash_key       = "documentId"

  # Define all attributes used by the key schema and any local/global secondary indexes
  attribute {
    name = "documentId"
    type = "S" # S for String, N for Number, B for Binary
  }

  attribute {
    name = "dateOfPurchase"
    type = "S"
  }
  
  # Optional: Define a sort key
  range_key = "dateOfPurchase"

  # Optional: Enable Point-In-Time Recovery (PITR) for continuous backups
  #point_in_time_recovery {
  #  enabled = true
  #}

  tags = {
    Project     = "Receipt Uploader - Terraform"
  }
}