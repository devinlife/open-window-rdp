import boto3
import time
import subprocess
import sys

REGION = "ap-northeast-2"
INSTANCE_ID = "i-068bf298be44c95c4"  # EC2 인스턴스 ID
RDP_FILENAME = "MyInstance.rdp"
USERNAME = "Administrator"


ec2 = boto3.client("ec2", region_name=REGION)


def get_instance_state(instance_id):
    response = ec2.describe_instances(InstanceIds=[instance_id])
    return response["Reservations"][0]["Instances"][0]["State"]["Name"]


def start_instance(instance_id):
    print("🔄 인스턴스를 시작합니다...")
    ec2.start_instances(InstanceIds=[instance_id])
    waiter = ec2.get_waiter("instance_running")
    print("⏳ 인스턴스가 시작될 때까지 기다립니다...")
    waiter.wait(InstanceIds=[instance_id])
    print("✅ 인스턴스가 running 상태입니다.")


def stop_instance(instance_id):
    print("🔻 인스턴스를 중지합니다...")
    ec2.stop_instances(InstanceIds=[instance_id])
    waiter = ec2.get_waiter("instance_stopped")
    print("⏳ 인스턴스가 중지될 때까지 기다립니다...")
    waiter.wait(InstanceIds=[instance_id])
    print("✅ 인스턴스가 stopped 상태입니다.")


def get_instance_dns(instance_id):
    response = ec2.describe_instances(InstanceIds=[instance_id])
    instance = response["Reservations"][0]["Instances"][0]
    return instance.get("PublicDnsName", "N/A")


def generate_rdp_file(dns_name: str, filename: str = RDP_FILENAME):
    rdp_content = f"""auto connect:i:1
full address:s:{dns_name}
username:s:{USERNAME}
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(rdp_content)
    print(f"📝 RDP 파일 생성 완료: {filename}")


def open_rdp_file(filename: str):
    try:
        subprocess.run(["open", filename], check=True)
        print(
            "🚀 RDP 파일 실행 완료 (Microsoft Remote Desktop 앱이 설치되어 있어야 합니다)"
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ RDP 파일 실행 실패: {e}")


def handle_start():
    state = get_instance_state(INSTANCE_ID)
    print(f"📦 현재 인스턴스 상태: {state}")

    if state == "stopped":
        start_instance(INSTANCE_ID)
    elif state == "running":
        print("⚡ 이미 실행 중입니다.")
    else:
        print(f"❌ {state} 상태에서는 시작할 수 없습니다.")
        return

    time.sleep(5)  # DNS 할당 대기
    public_dns = get_instance_dns(INSTANCE_ID)

    if public_dns == "N/A":
        print("❌ 퍼블릭 DNS를 가져오지 못했습니다.")
        return

    print("\n🖥️ RDP 접속 정보:")
    print(f"  - Public DNS : {public_dns}")
    print(f"  - 연결주소   : {public_dns}:3389")

    generate_rdp_file(public_dns)
    open_rdp_file(RDP_FILENAME)


def handle_stop():
    state = get_instance_state(INSTANCE_ID)
    print(f"📦 현재 인스턴스 상태: {state}")

    if state == "running":
        stop_instance(INSTANCE_ID)
    elif state == "stopped":
        print("🛑 이미 중지된 상태입니다.")
    else:
        print(f"❌ {state} 상태에서는 중지할 수 없습니다.")


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ["start", "stop"]:
        print("❗ 사용법: python ec2_control.py [start|stop]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "start":
        handle_start()
    elif command == "stop":
        handle_stop()


if __name__ == "__main__":
    main()
