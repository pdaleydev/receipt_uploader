output "source_bucket" {
  value       = aws_s3_bucket.photo_upload_bucket.bucket
  description = "The name of the photo upload bucket."
}

output "dest_bucket" {
  value       = aws_s3_bucket.textract_json_dump_bucket.bucket
  description = "The name of the JSON data dump bucket."
}

output "source_bucket_arn" {
  value       = aws_s3_bucket.photo_upload_bucket.arn
  description = "The arn of the photo upload bucket."
}

output "dest_bucket_arn" {
  value       = aws_s3_bucket.textract_json_dump_bucket.arn
  description = "The arn of the JSON data dump bucket."
}


output "dynamo_table" {
  value       = aws_dynamodb_table.receipt_table.name
  description = "The name of the Dynamo DB containing receipt info."
}

output "dynamo_table_arn" {
  value       = aws_dynamodb_table.receipt_table.arn
  description = "The arn of the Dynamo DB containing receipt info."
}
