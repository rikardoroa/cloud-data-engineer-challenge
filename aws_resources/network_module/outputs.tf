output "subnet_group" {
  value = aws_db_subnet_group.rds.name
}

output "security_group" {
  value = aws_security_group.rds.id
}

output "subnet2" {
  value = aws_subnet.subnet2-t1-db-pg-private.id
}

output "security_group_lambda" {
  value = aws_security_group.lambda.id
}
