# Báo Cáo Đánh Giá & Tối Ưu Hóa Cấu Hình Ansible

Tài liệu này dựa trên review đánh giá trước đó, đã được cập nhật lại theo tình trạng thực tế **hiện tại** của mã nguồn sau các bản sửa lỗi (fix) gần nhất.

## 🌟 1. Những Điểm Tốt / Đúng Tư Duy DevSecOps
- **Dynamic Inventory (`aws_ec2.yml`)**: Việc không hard-code IP tĩnh mà dùng AWS EC2 plugin để query tự động qua thẻ `tag` (Project, Environment, Role) là chính xác.
- **SSM Connection**: Kết nối qua `amazon.aws.aws_ssm` thay vì SSH port 22 là một best-practice tuyệt vời về bảo mật, giảm thiểu tối đa rủi ro lộ public IP/SSH keys.
- **Biến Region động**: Việc dùng `lookup('env', 'AWS_REGION')` giúp code Ansible có thể linh hoạt chạy ở nhiều vùng khác nhau mà không phải sửa code.

---

## ✅ 2. Những Cảnh Báo Cũ Đã Được Khắc Phục Lỗi
- **Cấu trúc `site.yml` sai cú pháp**: Đã được sửa. Lệnh `import_playbook` đã được kéo ra top-level (cùng cấp với cấu hình playbook rễ), không còn bị đặt nhầm vào bên trong `tasks:` cấu hình role nữa.
- **Tên file không đồng nhất**: Lỗi gọi nhầm `deploy_app.yml` thay vì file thực tế của ứng dụng đã được sửa bằng cách đổi hoàn toàn thành `deploy_log_analyzer.yml`.
- **Lỗi thiếu Handlers**: Review cũ cho rằng không có `handlers` đi kèm lệnh `notify: Restart Server`. Thực tế khi kiểm tra lại role `ec2_setup`, file `handlers/main.yml` **đã tồn tại** và cấu hình module `reboot` hợp lệ.

---

## ✅ 3. Danh Sách Những Mục ĐÃ SỬA XONG (All Action Items Completed)

### ✅ Cải thiện `inventory/aws_ec2.yml`
- [x] **Bổ sung alias/name dễ nhìn cho debugging**: Đã thêm `tag:Name` và `private-ip-address` vào danh sách `hostnames` (fallback chain: Name → Private IP → Instance ID). Log Ansible giờ sẽ hiển thị tên máy hoặc IP nội bộ dễ nhìn hơn.
- [x] **Làm động Environment**: Đã đổi `"tag:Environment": dev` thành `"tag:Environment": "{{ lookup('env', 'ENV_NAME') | default('dev', true) }}"`. Khi chạy pipeline chỉ cần set `ENV_NAME=staging` hoặc `ENV_NAME=prod` là Ansible tự chuyển môi trường.

### ✅ Cải thiện `install_docker.yml`
- [x] **Thêm `python3-pip` vào danh sách yum packages**: Đảm bảo hệ thống có trình quản lý gói Python.
- [x] **Cài Python Docker SDK**: Đã bổ sung task `pip install docker docker-compose` qua module `pip`. Đây là yêu cầu bắt buộc để các module `community.docker.docker_image` và `community.docker.docker_container` hoạt động.

### ✅ Cải thiện `deploy_log_analyzer.yml`
- [x] **Thay `shell` bằng `community.docker` modules**: Đã viết lại hoàn toàn:
  - `community.docker.docker_image` (source: build) thay cho `docker build`.
  - `community.docker.docker_container` (state: started, recreate: yes) thay cho `docker rm -f` + `docker run`.
- [x] **Đảm bảo tính Idempotent**: Module `docker_container` với `recreate: yes` sẽ tự xóa container cũ và tạo lại, chạy bao nhiêu lần cũng cho kết quả nhất quán.
- [x] **Thêm `restart_policy: unless-stopped`**: Container sẽ tự khởi động lại nếu EC2 bị reboot.
- [x] **Dùng `playbook_dir`**: Đường dẫn copy source code giờ dùng `{{ playbook_dir }}` thay vì đường dẫn tương đối cứng (`../../`), ổn định hơn khi chạy từ CI/CD pipeline.
- [x] **Volume mount read-only (`:ro`)**: File `.env` được mount vào container ở chế độ chỉ đọc, tăng bảo mật.

### ✅ Cải thiện Role `ec2_setup/tasks/main.yml`
- [x] **Loại bỏ `yum: name: "*", state: latest`**: Đã thay bằng 2 task riêng biệt:
  1. `yum: update_cache: yes` — chỉ cập nhật bộ nhớ cache danh sách gói, không nâng cấp bất kỳ gói nào.
  2. `yum: name: [curl, wget, unzip, jq, awscli], state: present` — cài đặt danh sách gói thiết yếu cụ thể, phiên bản ổn định.
- [x] **Security Patches có điều kiện**: Thêm task `yum: security: yes, state: latest` nhưng chỉ chạy khi biến `apply_security_patches` được set `true`. Mặc định là `false` trong `group_vars/all.yml`. Điều này giúp DevOps chủ động kiểm soát Patch Management thay vì bị update bất ngờ.

### ✅ Cải thiện Cơ chế Secrets Management
- [x] **Tạo `inventory/group_vars/all.yml`**: File này cung cấp tất cả biến mặc định (`aws_region`, `bedrock_model`, `max_tokens`, `temperature`, `app_port`, `apply_security_patches`) cho toàn bộ host. Template `app.env.j2` giờ đã có nguồn biến rõ ràng.
- [x] **Hướng dẫn Secrets Management**: Trong `group_vars/all.yml` đã ghi rõ 3 phương pháp quản lý secret an toàn:
  1. **Ansible Vault** — mã hóa file `vault.yml` cho dự án nhỏ.
  2. **AWS SSM Parameter Store** — dùng `lookup('amazon.aws.aws_ssm', ...)`.
  3. **AWS Secrets Manager** — dùng `lookup('amazon.aws.aws_secret', ...)`.

---

## 📁 Cấu Trúc Thư Mục Ansible Sau Khi Tối Ưu

```
ansible/
├── ansible.cfg                         # Cấu hình chính
├── requirements.yml                    # Collections: amazon.aws, community.docker
├── inventory/
│   ├── aws_ec2.yml                     # 🔧 SỬA — Dynamic inventory (ENV động, hostname dễ đọc)
│   └── group_vars/
│       └── all.yml                     # ✨ MỚI — Biến mặc định + hướng dẫn secrets
├── playbooks/
│   ├── site.yml                        # Master playbook (đã sửa cấu trúc import)
│   ├── install_docker.yml              # 🔧 SỬA — Thêm Python Docker SDK
│   └── deploy_log_analyzer.yml         # 🔧 SỬA — Dùng community.docker modules
├── roles/
│   └── ec2_setup/
│       ├── tasks/main.yml              # 🔧 SỬA — Cài gói cụ thể, patch có điều kiện
│       ├── handlers/main.yml           # Handler reboot (không đổi)
│       ├── defaults/
│       ├── templates/
│       └── vars/
└── templates/
    └── app.env.j2                      # Template biến Bedrock (đã sửa trước đó)
```
