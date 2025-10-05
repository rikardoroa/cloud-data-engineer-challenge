resource "aws_db_instance" "postgres" {
  engine                                = "postgres"
  identifier                            = "dbgeospatialdev"
  allocated_storage                     = 20
  max_allocated_storage                 = 100
  engine_version                        = "15.7"
  instance_class                        = "db.t4g.small"
  username                              = "postgres"
  password                              = var.db_password
  vpc_security_group_ids                = [var.security_group]
  db_subnet_group_name                  = var.subnet_group
  multi_az                              = true
  skip_final_snapshot                   = true
  storage_encrypted                     = true
  backup_retention_period               = 7
  deletion_protection                   = false
  auto_minor_version_upgrade            = true
  performance_insights_enabled          = true
  performance_insights_retention_period = 7
}

resource "aws_secretsmanager_secret" "rds_secret_postgresql" {
  name                    = "postgresql_conn"
  description             = "RDS credentials for geospatialdev database"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "rds_secret_value_db" {
  secret_id = aws_secretsmanager_secret.rds_secret_postgresql.id
  secret_string = jsonencode({
    username = "postgres"
    password = var.db_password
    host     = aws_db_instance.postgres.endpoint
    port     = aws_db_instance.postgres.port
    dbname   = "postgres"
  })
}