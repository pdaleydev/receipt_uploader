variable "aws_region" {
  type    = string
  default = "us-east-2"
}

variable "aws_user" {
  type    = string
}

variable "project_name" {
  type = string
  default = "MyProject"
}

variable "workspace_path" {
  type = string
}

variable "latest_triggerTextract" {
  type    = string
  default = "triggerTextract_v2"
}

