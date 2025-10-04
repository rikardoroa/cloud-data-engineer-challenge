# --- VPC ---
resource "aws_vpc" "vpc-t1-db-pg" {
  cidr_block = "10.0.0.0/17"
}

# --- subnets ---
resource "aws_subnet" "subnet1-t1-db-pg-public" {
  vpc_id                  = aws_vpc.vpc-t1-db-pg.id
  cidr_block              = "10.0.64.0/19"
  map_public_ip_on_launch = true
  availability_zone       = "us-east-2a"
}

resource "aws_subnet" "subnet2-t1-db-pg-private" {
  vpc_id            = aws_vpc.vpc-t1-db-pg.id
  cidr_block        = "10.0.96.0/20"
  availability_zone = "us-east-2a"
}

resource "aws_subnet" "subnet3-t1-db-pg-private" {
  vpc_id            = aws_vpc.vpc-t1-db-pg.id
  cidr_block        = "10.0.112.0/21"
  availability_zone = "us-east-2b"
}

# --- Internet Gateway ---
resource "aws_internet_gateway" "igt-t1-db" {
  vpc_id = aws_vpc.vpc-t1-db-pg.id
}

# --- Elastic Ip and NAT Gateway ---
resource "aws_eip" "nat-eip-t1-db" {
  domain = "vpc"
}

resource "aws_nat_gateway" "nat-t1-db" {
  allocation_id = aws_eip.nat-eip-t1-db.id
  subnet_id     = aws_subnet.subnet1-t1-db-pg-public.id
}

# --- Public Route Table ---
resource "aws_route_table" "rt-t1-db-public" {
  vpc_id = aws_vpc.vpc-t1-db-pg.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igt-t1-db.id
  }
}

resource "aws_route_table_association" "asc-t1-db-public" {
  subnet_id      = aws_subnet.subnet1-t1-db-pg-public.id
  route_table_id = aws_route_table.rt-t1-db-public.id
}

# --- Private Route Table ---
resource "aws_route_table" "rt-t1-db-private" {
  vpc_id = aws_vpc.vpc-t1-db-pg.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat-t1-db.id
  }
}

resource "aws_route_table_association" "asc-t1-db-private" {
  subnet_id      = aws_subnet.subnet2-t1-db-pg-private.id
  route_table_id = aws_route_table.rt-t1-db-private.id
}

resource "aws_route_table_association" "asc-t1-db-private2" {
  subnet_id      = aws_subnet.subnet3-t1-db-pg-private.id
  route_table_id = aws_route_table.rt-t1-db-private.id
}

# --- Security Groups ---
resource "aws_security_group" "lambda" {
  vpc_id = aws_vpc.vpc-t1-db-pg.id
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "rds" {
  vpc_id = aws_vpc.vpc-t1-db-pg.id
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# --- RDS Subnet ---
resource "aws_db_subnet_group" "rds" {
  name = "rds-subnet-group"
  subnet_ids = [
    aws_subnet.subnet2-t1-db-pg-private.id,
    aws_subnet.subnet3-t1-db-pg-private.id
  ]
}