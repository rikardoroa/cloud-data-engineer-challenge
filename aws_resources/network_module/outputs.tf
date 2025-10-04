output "subnet_group"{
    value = aws_db_subnet_group.rds.name
}

output "security_group" {
    value = aws_security_group.rds.id
}