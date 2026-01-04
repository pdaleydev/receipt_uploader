data "terraform_remote_state" "data_stores" {
  backend = "local"
  config = {
    path = "../data_stores/terraform.tfstate"
  }
}

data "terraform_remote_state" "permissions" {
  backend = "local"
  config = {
    path = "../permissions/terraform.tfstate"
  }
}

data "archive_file" "triggerTextract_code" {
  type        = "zip"
  source_file = "${var.workspace_path}/src/triggerTextract_v2.py"
  output_path = "${var.workspace_path}/output/triggerTextract_v2.zip"
}
