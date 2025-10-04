resource "aws_db_instance" "postgres" { 
    engine = "Postgres" 
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