resource "aws_db_instance" "postgres" {
  engine = "postgres"
  identifier = "dbgeospatialdev"
  allocated_storage = 20
  engine_version = "15.7"
  instance_class = "db.t3.micro"
  username = "postgres"
  password = var.db_password
  vpc_security_group_ids = [var.security_group]
  db_subnet_group_name = var.subnet_group
  skip_final_snapshot = true
}

resource "aws_secretsmanager_secret" "rds_secret" {
  name = "postgresql_conn"
  description = "RDS credentials for geospatialdev database"
}

resource "aws_secretsmanager_secret_version" "rds_secret_value" {
  secret_id = aws_secretsmanager_secret.rds_secret.id
  secret_string = jsonencode({
    username = "postgres"
    password = var.db_password
    host = aws_db_instance.postgres.endpoint
    port = aws_db_instance.postgres.port
    dbname = "postgres"
  })
}
