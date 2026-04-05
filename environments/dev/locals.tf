data "aws_availability_zones" "available" {
    state = "available"
}

variable "tags" {
  description = "Additional tags to merge"
  type        = map(string)
  default     = {}  
}

locals {
    name_prefix = "${var.project}-${var.env}-${var.region_short}"
    ports = { http = 80, https = 443, app = 8080, db = 5432 }

    azs = data.aws_availability_zones.available.names
}

