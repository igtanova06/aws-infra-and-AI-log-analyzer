import boto3

REGION = 'ap-southeast-1'
LOG_GROUPS = [
    '/aws/vpc/flowlogs',
    '/aws/cloudtrail/logs',
    '/aws/ec2/application',
    '/aws/rds/mysql/error',
    '/aws/rds/mysql/slowquery'
]
LOG_STREAM_NAME = 'omni-stream-prod'

client = boto3.client('logs', region_name=REGION)

print("Đang xóa log cũ...")
for group in LOG_GROUPS:
    try:
        client.delete_log_stream(logGroupName=group, logStreamName=LOG_STREAM_NAME)
        print(f"✅ Đã xóa stream {LOG_STREAM_NAME} trong {group}")
    except client.exceptions.ResourceNotFoundException:
        print(f"ℹ️ Stream {LOG_STREAM_NAME} không tồn tại trong {group}, bỏ qua.")
    except Exception as e:
        print(f"❌ Lỗi khi xóa {group}: {e}")

print("\nHoàn tất! Bây giờ bạn có thể chạy `python generate_omni_logs.py` để tạo log mới sạch sẽ.")
