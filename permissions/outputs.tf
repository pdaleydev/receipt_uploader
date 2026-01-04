output "role_arn" {
  value       = aws_iam_role.lambda_role.arn
  description = "The arn of the IAM role that triggerTextract will assume."
}
