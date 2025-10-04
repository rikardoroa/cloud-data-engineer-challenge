resource "aws_db_instance" "postgres" { 
    identifier = var.db_name
    engine = "postgres" 
    engine_version = "15.7" 
    instance_class = "db.t3.micro" 
    allocated_storage = 20 
    db_name = var.db_name
    username = var.db_user
    password = var.db_password
    vpc_security_group_ids = [var.security_group] 
    db_subnet_group_name = var.subnet_group
    skip_final_snapshot = true 
   }