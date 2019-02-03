data "aws_caller_identity" "current" {}

provider "aws" {
  region = "${var.region}"
}

terraform {
  backend "s3" {
    bucket   = "temp-lambda-files"
    key      = "states/rewbot_lambda/terraform.tfstate"
    region   = "us-west-2"
  }
}
