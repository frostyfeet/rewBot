data "template_file" "iam_assume_role_lambda" {
  template = "${file("policies/iam_assume_role.json")}"

  vars {
    aws_service = "lambda"
  }
}

data "template_file" "rewbot_lambda_policy" {
  template = "${file("./policies/rewbot_lambda.json")}"
}

resource "aws_cloudwatch_event_rule" "rewbot_lambda" {
  name        = "rewbot_events"
  description = "Cron for lambda"

  schedule_expression = "rate(30 minutes)" 
}

resource "aws_lambda_permission" "rewbot_lambda" {
  statement_id  = "rewbot-lambda-trigger"
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.rewbot_lambda.function_name}"
  principal     = "events.amazonaws.com"
  source_arn    = "${aws_cloudwatch_event_rule.rewbot_lambda.arn}"
}

resource "aws_cloudwatch_event_target" "rewbot_to_lambda" {
  rule = "${aws_cloudwatch_event_rule.rewbot_lambda.name}"
  arn  = "${aws_lambda_function.rewbot_lambda.arn}"
}

resource "aws_lambda_function" "rewbot_lambda" {
  filename         = "./build/lambda.zip"
  function_name    = "rewbot_lambda"
  description      = "Updates the rewbots"
  runtime          = "python3.7"
  role             = "${aws_iam_role.rewbot_lambda_role.arn}"
  handler          = "rewbot.handler"
  source_code_hash = "${base64sha256(file("./build/lambda.zip"))}"
  memory_size      = 128 
  timeout          = 900

  tags {
    "Contact"     = "${var.contact}"
    "Service"     = "${var.service}"
    "Description" = "Managed via Terraform"
    "Environment" = "${var.env}"
  }
}

resource "aws_iam_role_policy_attachment" "rewbot_lambda_policy_att" {
  role       = "${aws_iam_role.rewbot_lambda_role.name}"
  policy_arn = "${aws_iam_policy.rewbot_lambda_policy.arn}"
}

resource "aws_iam_role_policy_attachment" "rewbot_lambda_policy_att_basic" {
  role       = "${aws_iam_role.rewbot_lambda_role.name}"
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "rewbot_lambda_policy" {
  name        = "rewbot_lambda_policy"
  description = "Grants access to describe instances"
  policy      = "${data.template_file.rewbot_lambda_policy.rendered}"
}

resource "aws_iam_role" "rewbot_lambda_role" {
  name               = "rewbot_lambda_role"
  assume_role_policy = "${data.template_file.iam_assume_role_lambda.rendered}"
}
