resource "aws_s3_bucket" "photo_upload_bucket" {
  bucket = var.source_bucket

  tags = {
    Project = var.project_name
  }
}

resource "aws_s3_bucket" "textract_json_dump_bucket" {
  bucket = var.dest_bucket

  tags = {
    Project = var.project_name
  }
}