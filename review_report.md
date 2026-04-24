# 🚀 Báo Cáo Review Kiến Trúc DevSecOps (Terraform & Ansible)

Chào bạn, mình đã xem kỹ toàn bộ cấu trúc dự án (Terraform & Ansible) với tư duy **DevSecOps**. Mình nhận thấy bạn đã có một foundation rất tốt, nhưng để đạt được chuẩn bảo mật cao nhất, tối ưu hoá tốt nhất, phân tách Layer rõ ràng, và liên kết được với Database có sẵn, dưới đây là các phân tích và gợi ý sửa lỗi chi tiết để bạn có thể tự review lại code.

---

## 1. 🏗️ Phân Tách Layer (Web Node & App Node) & Bảo Mật Access (SSM)

**Tình trạng hiện tại:**
- **Layer 1 (Web QLSV)** và **Layer 2 (AI Log Analysis)** đều đang được gán vào ALB (Application Load Balancer).
- Security Group của Layer 2 (`aws_security_group.app`) đang mở port 80 để nhận traffic trực tiếp từ ALB (`app_from_alb`).
- Như vậy, Layer 2 đang bị phơi ra internet thông qua Load Balancer thay vì hoàn toàn private như thiết kế an toàn.

**Mục tiêu của bạn:** 
Tách bạch Layer 1 (chỉ phục vụ web) và Layer 2 (chạy nội bộ, chỉ kết nối bằng SSM port forwarding cho máy Admin).

**Gợi ý sửa đổi:**

1. **Trong `environments/dev/alb.tf`:**
   - **Xóa bỏ** `aws_lb_target_group.app` (Target Group cho Log Analyzer).
   - Đổi `default_action` của `aws_lb_listener.app` thành trả về lỗi 404 (Fixed Response) thay vì trỏ vào Layer 2. Điều này đảm bảo những request rác/không hợp lệ tới ALB sẽ bị chặn ngay lập tức.
   ```hcl
   # Gợi ý: Sửa lại default action trong alb.tf
   default_action {
     type = "fixed-response"
     fixed_response {
       content_type = "text/plain"
       message_body = "404: Not Found"
       status_code  = "404"
     }
   }
   ```

2. **Trong `environments/dev/compute.tf`:**
   - Tại block `aws_autoscaling_group.app` (Layer 2), **xóa dòng** `target_group_arns = [aws_lb_target_group.app.arn]` để tách hoàn toàn Layer 2 khỏi ALB.

3. **Trong `environments/dev/security_groups.tf` (Rất Quan Trọng):**
   - **Xóa** toàn bộ inbound rule `aws_vpc_security_group_ingress_rule.app_from_alb`.
   - Vì Layer 2 sẽ kết nối bằng **AWS Systems Manager (SSM) Session Manager**, bạn KHÔNG CẦN mở bất kỳ cổng Inbound nào (như SSH port 22 hay HTTP 80) từ bên ngoài. SSM Agent trên máy chủ sẽ chủ động gọi ra ngoài (Outbound) tới AWS SSM Endpoints. 
   - Rule Outbound hiện tại `app_egress` (đi `0.0.0.0/0`) là đã đủ, hoặc nếu dùng VPC Endpoints thì chỉ cần cho phép gọi tới cổng 443 của SSM.

4. **Cách Admin kết nối vào Layer 2 (SSM Port Forwarding):**
   - Khi cần truy cập vào Streamlit UI, Admin sẽ chạy lệnh sau trên máy tính (yêu cầu cài AWS CLI + Session Manager Plugin):
     ```bash
     aws ssm start-session \
         --target <INSTANCE_ID_CỦA_LAYER_2> \
         --document-name AWS-StartPortForwardingSession \
         --parameters "{\"portNumber\":[\"80\"],\"localPortNumber\":[\"8080\"]}"
     ```
   - Truy cập `http://localhost:8080` an toàn tuyệt đối.

---

## 2. 🗄️ Tối Ưu Database (Link với RDS Hiện Có)

**Tình trạng hiện tại:**
- File `environments/dev/database.tf` đang tự động tạo ra một RDS hoàn toàn mới (`aws_db_instance.main`).
- Mật khẩu tạo ngẫu nhiên nhưng file Code PHP ở `Web-Project-1/api/db.php` lại đang "hardcode" endpoint cố định: `$db_host = "p1-dev-apse1-db.cvmygmiqa7t4.ap-southeast-1.rds.amazonaws.com"`.
- Cổng Database trong `locals.tf` đang bị nhầm lẫn là `5432` (PostgreSQL) trong khi RDS tạo ra là MySQL.

**Gợi ý sửa đổi:**

1. **Trong `environments/dev/database.tf`:**
   - Nếu bạn đã có DB rồi, **hãy xóa bỏ** các block tạo DB (`aws_db_instance`, `random_password`).
   - Sử dụng `Data Source` để lấy thông tin của RDS hiện tại để dùng cho các config khác:
     ```hcl
     # Gợi ý code lấy DB đã có
     data "aws_db_instance" "existing_db" {
       db_instance_identifier = "p1-dev-apse1-db" # Có thể biến thành variable
     }
     ```

2. **Trong `environments/dev/security_groups.tf` (Sửa rule của DB):**
   - Sửa `aws_vpc_security_group_ingress_rule.db_from_app_postgres`:
     - Tên nên đổi lại là `db_from_web_mysql`.
     - `referenced_security_group_id`: Phải đổi từ `aws_security_group.app.id` (Layer 2) thành `aws_security_group.web.id` (Layer 1). Bởi vì Layer 1 (PHP) mới là thằng gọi vào database QLSV.
     - `from_port` và `to_port` phải là `3306` thay vì gọi vào biến port `5432` sai.

3. **Trong ứng dụng PHP (`Web-Project-1/api/db.php`):**
   - **Tư duy DevSecOps:** Tuyệt đối không để chuỗi kết nối (`db_host`, password) thẳng trong source code đẩy lên Git.
   - Hãy đổi thành đọc biến môi trường:
     ```php
     $db_host = getenv('DB_HOST') ?: "localhost";
     $db_user = getenv('DB_USER');
     $db_pass = getenv('DB_PASS');
     ```
   - Trong quá trình deploy bằng Ansible, bạn truyền biến này vào Docker container của app.

---

## 3. ⚠️ Hard Code & Các Lỗi Không Tối Ưu Khác

### A. Trong Terraform
- **`alb.tf`**: Tại `aws_lb_listener_rule.qlsv`, path patterns `/qlsv*`, `/api/*` đang bị hard code. Khá rủi ro nếu ứng dụng thay đổi endpoint. Nên chuyển chúng vào một list biến trong `variables.tf`.
- **`locals.tf`**: Sửa port database từ `db = 5432` thành `db = 3306` cho nhất quán với kiến trúc dùng MySQL.
- **`compute.tf`**: Instance type đang bị cố định `t3.micro`. Nên đặt nó là một biến (ví dụ `var.instance_type_web` và `var.instance_type_app`) để dễ scale up lên khi cần.

### B. Trong Ansible (DevSecOps Mindset)
- **`ansible/playbooks/install_docker.yml`**:
  - Task "Check internet connectivity" bằng cách `ping -c 3 google.com` kết hợp với `ignore_errors: yes` là một bad practice. Bạn nên dùng module `wait_for` của Ansible để check port, hoặc check mirror của AWS/CentOS để đảm bảo độ ổn định.
  
- **`ansible/playbooks/deploy_log_analyzer.yml` (Nghiêm trọng về bảo mật):**
  - Trong command khởi chạy Streamlit, bạn đang sử dụng cờ:
    ```yaml
    --server.enableCORS=false
    --server.enableXsrfProtection=false
    ```
  - **DevSecOps Cảnh báo:** Việc tắt CORS và XSRF (Cross-Site Request Forgery) khiến giao diện phân tích có thể bị hacker đánh cắp phiên hoặc chèn mã độc.
  - **Gợi ý:** Vì bạn truy cập Log Analyzer thông qua SSM Port Forwarding (tức là truy cập qua `localhost:8080`), hãy **BỎ 2 cờ này đi** để dùng config bảo vệ mặc định của Streamlit. Bạn có thể set `--server.address=127.0.0.1` thay vì `0.0.0.0` để chặn truy cập lọt từ trong mạng VPC vào, chỉ cho duy nhất máy chủ cục bộ (SSM agent) gọi vào.

- **`ansible/playbooks/deploy_web_app.yml`**:
  - Source file đang bị trỏ đường dẫn tương đối `src: "../../Web-Project-1/"`. Cách tốt nhất trong Ansible CI/CD là đóng gói thành một tệp nén (.tar.gz), gửi sang EC2 rồi giải nén, hoặc pull trực tiếp bằng git từ một repository private kết hợp với Read-only Deploy Keys.

---

### Tổng kết các bước để bạn làm tiếp:
1. **Sửa Security Groups**: Chặt đứt liên kết từ ALB vào Layer 2. Mở cổng 3306 cho Layer 1 gọi vào DB.
2. **Sửa Load Balancer**: Xóa Target Group Layer 2. Setup 404 cho rác.
3. **Sửa DB Config**: Sửa Terraform dùng DB cũ thay vì tạo mới, sửa PHP dùng biến môi trường.
4. **Sửa luồng chạy Docker Streamlit**: Bật lại tính năng chặn XSRF và CORS để đảm bảo an toàn tối đa.

Bạn cứ thoải mái rà soát lại các file trên và tiến hành sửa nhé! Cần hỗ trợ thêm về bước nào cứ nhắn lại mình!
