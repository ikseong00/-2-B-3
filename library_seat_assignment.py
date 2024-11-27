import os.path
import csv
import re
import sys
import datetime
from typing import Optional

'''
전역변수
'''
ADMIN_ID_SYNTAX_PATTERN = '^[a-z0-9]{8,12}$'
PASSWORD_SYNTAX_PATTERN = '^[가-힣a-zA-Z0-9]{8,12}$'
USER_NAME_SYNTAX_PATTERN = '^[가-힣a-zA-Z]+$'
USER_ID_SYNTAX_PATTERN = r'^20([1-9]\d)\d{5}$'
SEAT_NUMBER_SYNTAX_PATTERN = r'^[1-9]\d*$'
TIME_SYNTAX_PATTERN = r"[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1]) (2[0-3]|[01][0-9]):[0-5][0-9]$"
SEAT_STATUS_SYNTAX_PATTERN="^[OXD]$"
READING_ROOM_NUMBER_SYNTAX_PATTERN = r'^[1-9]\d*$'
READING_ROOM_SEAT_LIMIT_SYNTAX_PATTERN = r'^[1-9]\d*$'
ASSIGNMENT_LOG_RECORD_TYPE_SYNTAX_PATTERN = r'^(reserve|return)$'

ADMIN_DATA_FILE = "libary_admin_data.csv" 
USER_DATA_FILE = "libary_user_data.csv"
SEAT_DATA_FILE = "library_seat_data.csv"
INPUT_TIME_FILE = "library_input_time_data.csv"
SEAT_ASSIGNMENT_LOG_FILE = "library_seat_assignment_log.csv"
READING_ROOM_DATA_FILE = "library_reading_room_data.csv"
 
### 2차 재설계 과정에서 추가된 전역 변수 ###
RESERVE = "reserve"
RETURN = "return"

max_uses_per_day = 3           ### 요구사항 E [3차 요구사항 대비] 전역 변수로 관리해서 관리자가 수정할 수 있음
max_recent_usage_day = 5       ### 요구사항 D [3차 요구사항 대비] 전역 변수로 관리해서 관리자가 수정할 수 있음
recent_days = 7 ### 요구사항 D [3차 요구사항 대비] 전역 변수로 관리해서 관리자가 수정할 수 있음

reading_room_list = []
recent_input_time = ""
library_system = None

class User:
    # User class 생성자
    def __init__(self, student_id: str, name: str, password: str, last_login_time: Optional[str] = None):

        self.student_id = student_id
        self.name = name
        self.password = password
        self.last_login_time = last_login_time
    
    # 로그인 시간 업데이트
    def update_login_time(self, current_time: str) -> None:
        self.last_login_time = current_time

    def get_user_info(self) -> dict:
        return {
            "student_id": self.student_id,
            "name": self.name,
            "password": self.password,
            "last_login_time": self.last_login_time
        }
 
class Admin:
    def __init__(self, id): # ** 
        self.id = id   # 관리자 아이디

    def change_reading_room_limit(self):
        print("열람실 최대 좌석 수 변경")

        # 현재 열람실 정보 출력
        print("현재 열람실 정보:")
        for room in reading_room_list:
            room_number = room[0]
            max_seats = room[1]
            current_seats = sum(1 for seat in library_system.get_seats() if seat[1] == room_number and seat[2] != "D")
            print(f"[{room_number}, {max_seats}, {current_seats}]")

        while True:
            try:
                # 변경할 열람실 번호와 새로운 최대 좌석 수 입력
                input_data = input("변경할 열람실 번호와 새로운 최대 좌석 수를 입력 ex) 1 100 > ").strip()
                room_number, max_seats = map(int, input_data.split())

                room_to_change = next((room for room in reading_room_list if room[0] == room_number), None)
                if not room_to_change:
                    print("존재하는 열람실 번호를 입력하세요.")
                    continue

                current_seats = sum(
                    1 for seat in library_system.get_seats() if seat[1] == room_number and seat[2] != "D")
                if max_seats < current_seats:
                    print("현재 존재하는 좌석 수보다 큰 값을 입력하세요.")
                    continue

                # 최대 좌석 수 변경
                room_to_change[1] = max_seats
                self.save_reading_room_data()
                break
            except ValueError:
                print("올바른 인자를 입력하세요. ex) 1 100")
                continue

    def add_seats(self):
        """좌석 추가 함수"""
        print("좌석 추가")
        while True:
            # 열람실 정보 출력
            print("도서관 열람실 현황:")
            for room in reading_room_list:
                print(f"[{room[0]}, {room[1]}]")

            room_number = input("좌석 추가를 진행할 열람실 번호 입력 > ")
            if not re.match(READING_ROOM_NUMBER_SYNTAX_PATTERN, room_number):
                print("유효한 열람실 번호를 입력하세요.")
                continue

            room_number = int(room_number)
            room_to_add = next((room for room in reading_room_list if room[0] == room_number), None)
            if not room_to_add:
                print("존재하는 열람실 번호를 입력하세요.")
                continue

            library_system.show_seat_status(room_number)

            seat_numbers = input("추가할 좌석 번호 입력 > ").split()
            now_seats = library_system.get_seats()
            current_seats = sum(1 for seat in now_seats if seat[1] == room_number and seat[2] != "D")
            max_seats = room_to_add[1]

            # 전체 입력 유효성 검사
            if len(seat_numbers) + current_seats > max_seats:
                print(f"최대 좌석 추가 한도를 초과하여 좌석을 추가할 수 없습니다.")
                break

            added_any = False

            for seat_number in seat_numbers:
                if not re.match(SEAT_NUMBER_SYNTAX_PATTERN, seat_number):
                    print(f"{seat_number}는 올바르지 않은 번호입니다.")
                    continue

                seat_number = int(seat_number)

                # 이미 존재하거나 복구 가능한 좌석 확인
                seat_to_restore = next(
                    (seat for seat in now_seats if seat[0] == seat_number and seat[1] == room_number), None)
                if seat_to_restore:
                    if seat_to_restore[2] == "D":
                        seat_to_restore[2] = "O"
                        print(f"{seat_number}번 좌석이 추가되었습니다.")
                    else:
                        print(f"이미 존재하는 좌석이기 때문에 {seat_number}번 좌석을 추가할 수 없습니다.")
                    continue
                else:
                    now_seats.append([seat_number, room_number, "O", '0000-10-29 10:31', '201000000'])
                    print(f"{seat_number}번 좌석이 추가되었습니다.")
                    added_any = True

            if added_any:
                library_system.save_seat_data()

            # 작업 완료 후 관리자 프롬프트로 복귀
            break

    def remove_seats(self):
        """좌석 삭제 함수"""
        print("좌석 삭제")
        while True:
            print("도서관 열람실 현황:")
            for room in reading_room_list:
                print(f"[{room[0]}, {room[1]}]")

            room_number = input("좌석 삭제를 진행할 열람실 번호 입력 > ")
            if not re.match(READING_ROOM_NUMBER_SYNTAX_PATTERN, room_number):
                print("유효한 열람실 번호를 입력하세요.")
                continue

            room_number = int(room_number)
            room_to_remove = next((room for room in reading_room_list if room[0] == room_number), None)
            if not room_to_remove:
                print("존재하는 열람실 번호를 입력하세요.")
                continue

            library_system.show_seat_status(room_number)

            seat_numbers = input("삭제할 좌석 번호 입력 > ").split()
            now_seats = library_system.get_seats()

            # 유효한 좌석 번호만 필터링
            valid_delete_numbers = []
            for seat_number in seat_numbers:
                if not re.match(SEAT_NUMBER_SYNTAX_PATTERN, seat_number):
                    print(f"{seat_number}는 올바르지 않은 번호입니다.")
                    continue
                seat_number = int(seat_number)
                valid_delete_numbers.append(seat_number)

            # 현재 열람실에서 삭제 가능한 좌석 확인
            available_seats = [seat for seat in now_seats if seat[1] == room_number and seat[2] == "O"]
            current_seat_count = len(available_seats)

            # 삭제 가능한 좌석 중 실제 열람실에 존재하는 좌석만 필터링
            valid_delete_count = sum(
                1 for seat_number in valid_delete_numbers
                if any(seat[0] == seat_number and seat[1] == room_number and seat[2] == "O" for seat in now_seats)
            )

            # 삭제 후 남는 좌석 확인
            if current_seat_count - valid_delete_count < 1:
                print(f"남아있는 좌석이 1개 이하이므로 더 이상 좌석을 삭제할 수 없습니다.")
                break

            removed_any = False

            for seat_number in valid_delete_numbers:
                seat_to_remove = next(
                    (seat for seat in now_seats if seat[0] == seat_number and seat[1] == room_number), None)

                if seat_to_remove:
                    if seat_to_remove[2] == "O":
                        seat_to_remove[2] = "D"
                        print(f"{seat_number}번 좌석이 삭제되었습니다.")
                        removed_any = True
                    elif seat_to_remove[2] == "X":
                        print(f"{seat_number}번 좌석은 현재 사용 중이어서 삭제할 수 없습니다.")
                    else:
                        print(f"{seat_number}번 좌석은 존재하지 않습니다.")
                else:
                    print(f"{seat_number}번 좌석은 존재하지 않습니다.")

            if removed_any:
                library_system.save_seat_data()

            # 작업 완료 후 관리자 프롬프트로 복귀
            break

    def save_reading_room_data(self):
        """열람실 데이터 저장"""
        with open(READING_ROOM_DATA_FILE, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerows(reading_room_list)

class LibrarySystem:
    def __init__(self):
        self.seats = []
        self.user = None
        self.load_seat_data()

    def get_seats(self):
        return self.seats

    def load_seat_data(self):
        if os.path.exists(SEAT_DATA_FILE):
            with open(SEAT_DATA_FILE, "r") as f:
                reader = csv.reader(f)
                for record in reader:
                    if len(record) != 0:
                        self.seats.append([int(record[0]), int(record[1]), record[2], record[3], record[4]])

    def save_seat_data(self):
        with open(SEAT_DATA_FILE, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerows(self.seats)

    def show_seat_status(self, room_number=None, show_status_mode="default"):
        if room_number is None:
            room_number = int(input("조회할 열람실 번호를 입력하세요 > "))

        print(f"{room_number}번 열람실의 좌석 정보:")

        seats = []
        for seat in self.seats:
            if seat[1] == room_number:
                seats.append(seat)

        if show_status_mode == "default":
            STATUS_ROW_LENGTH = 10
            seat_count = 0
            seat_status = ""

            for seat in seats:
                seat_count += 1

                # 로그인 중인 사용자가 이용 중인 좌석이면 ★로 표시
                if seat[2] == "D" :
                    seat_count -= 1
                    continue

                # 사용자 정보가 있을 때만 ★ 표시
                if self.user and isinstance(self.user, User) and seat[4] == self.user.student_id:
                    # 로그인된 사용자가 본인의 좌석을 볼 경우 ★ 표시
                    seat_status += f"{seat[0]:2}: [★]   "
                else:
                    # 관리자가 조회하거나 사용자의 좌석이 아닌 경우
                    seat_status += f"{seat[0]:2}: [{seat[2]}]   "

                if seat_count % STATUS_ROW_LENGTH == 0:
                    seat_status += "\n"

            print(seat_status)
            
    def reserve_seat(self):
        if self.check_four_day_consecutive_usage():
            return
        if self.check_three_times_usage_per_day(): #### 요구사항 2E 구현 완료
            return
        if self.validate_recent_seat_usage(): ### 요구사항 2D 구현 완료
            return
        
        for seat in self.seats:
            if self.user.student_id == seat[4]:
                print("이용중인 좌석이 있습니다.\n")
                return
        while True:
            seat_number = input("좌석번호 입력> ")
            if re.match(SEAT_NUMBER_SYNTAX_PATTERN, seat_number) == None:
                continue
                
            # 좌석 정보 확인
            seat_number = int(seat_number)
            for seat in self.seats:
                if seat[0] == seat_number:
                    if seat[2] == 'O':
                        seat[2] = 'X'
                        seat[3] = recent_input_time
                        seat[4] = self.user.student_id
                        self.save_seat_data()
                        print("좌석배정이 완료되었습니다.")
                        # 예약 기록 저장
                        with open(SEAT_ASSIGNMENT_LOG_FILE, "a", newline='') as f:
                            writer = csv.writer(f)
                            writer.writerow([self.user.student_id, seat_number, seat[1], recent_input_time, RESERVE]) ## 배정 플래그
                        return
                    else:
                        break



    def cancel_reservation(self):
        cancel = any(seat[4] == self.user.student_id and seat[2] == 'X' for seat in self.seats)
        if cancel:
            while True:
                check_cancel = input("좌석을 반납하시겠습니까?(Y/N) > ")
                if check_cancel == "Y":
                    for seat in self.seats:
                        if seat[4] == self.user.student_id and seat[2] == 'X':
                            seat[2] = 'O' 
                            seat[3] = '0000-10-29 10:31'
                            seat[4] = '201000000'
                            self.save_seat_data()
                            with open(SEAT_ASSIGNMENT_LOG_FILE, "a") as f:
                                writer = csv.writer(f)
                                writer.writerow([self.user.student_id, seat[0], seat[1], recent_input_time, RETURN])
                            print("좌석 반납이 완료되었습니다.")
                            return
                elif check_cancel == "N":
                    print("좌석 반납이 완료되지 않았습니다.")
                    return
                else:
                    continue
        else:
            print("이용중인 좌석이 없기 때문에 좌석 반납을 실행할 수 없습니다.")
            return
        
    def check_expired_reservations(self, now_time): # 통합 중 수정 : 누락된 인자 추가
        current_time = datetime.datetime.strptime(recent_input_time, "%Y-%m-%d %H:%M")
        MAX_USAGE_TIME = 3*60*60 #이변수로 자동반납 시간 결정 가능.
        for seat in self.seats:
            if seat[2] == 'X' and seat[3] != '':
                reserve_time = datetime.datetime.strptime(seat[3], "%Y-%m-%d %H:%M")
                if (current_time - reserve_time).total_seconds() > MAX_USAGE_TIME: 
                    with open(SEAT_ASSIGNMENT_LOG_FILE, "a") as f:
                        writer = csv.writer(f)
                        returned_time = reserve_time + datetime.timedelta(hours=3)
                        writer.writerow([seat[4], seat[0], seat[1], returned_time.strftime("%Y-%m-%d %H:%M"), RETURN])
                    seat[2] = 'O'
                    seat[3] = '0000-10-29 10:31'
                    seat[4] = '201000000'
        self.save_seat_data()

    def max_seat_detect(self, seat_number: int=1, room_number: int=1 ) -> bool:
        
        max_seat_limit = next((limit[1] for limit in reading_room_list if limit[0] == room_number), None)
        current_seat_count = sum(1 for seat in library_system.get_seats() if seat[1] == room_number and seat[2] != "D")
        total_number = current_seat_count + seat_number
        if total_number <= max_seat_limit:
            return True
        else:
            return False
    
    def check_four_day_consecutive_usage(self) -> bool:
        ## ** 재설계문서 [수정 필요] : 내용 약간 수정 필요
        current_time = datetime.datetime.strptime(recent_input_time, "%Y-%m-%d %H:%M").replace(hour=1, minute=1)
        MAX_CONSECUTIVE_DAYS = 3  # 확장성 고려. 이변수로 n일연속여부 체크가능.
        consecutive_usage_limit_exceeded = False

        reservations = []
        with open(SEAT_ASSIGNMENT_LOG_FILE, "r") as f:
            reader = csv.reader(f)
            for record in reader:
                if len(record) != 0:
                    if record[0] == self.user.student_id and record[4] == RESERVE: # 배정 플래그 확인
                        reservation_time = datetime.datetime.strptime(record[3], "%Y-%m-%d %H:%M").replace(hour=1, minute=1)
                        reservations.append(reservation_time)
        reservations.append(current_time)

        if len(reservations) < MAX_CONSECUTIVE_DAYS:
            return False
        
        # print("debug : current_time = ", current_time)
        # print("debug : reservations[-1] = ", reservations[-1])
            
        reservations.sort()

        # print("debug : reservations = ", reservations)

        consecutive_day_count = 0   
        for i in range(len(reservations) - 1, 1, -1):
            if (reservations[i] - reservations[i - 1]).days == 1:
                consecutive_day_count += 1
                if consecutive_day_count >= MAX_CONSECUTIVE_DAYS:
                    print(f"{MAX_CONSECUTIVE_DAYS + 1}일 연속 좌석을 배정할 수 없습니다.")
                    consecutive_usage_limit_exceeded = True
                    break
            elif (reservations[i] - reservations[i - 1]).days > 1:
                break
        
        return consecutive_usage_limit_exceeded
    
    def check_three_times_usage_per_day(self) -> bool:
        '''
        요구사항 2E
        '''
        current_date = datetime.datetime.strptime(recent_input_time, "%Y-%m-%d %H:%M").date()
        # MAX_USES_PER_DAY = 3  # 새로운 요구사항에 대비하기 위해서 전역변수로 전환
        usage_count = 0
        with open(SEAT_ASSIGNMENT_LOG_FILE, "r") as f:
            reader = csv.reader(f)
            for record in reader:
                if len(record) != 0:
                    if record[0] == self.user.student_id and record[4] == RESERVE:  # 현재 사용자 학번과 동일한 기록만 체크 # 배정 플래그 확인
                        reservation_date = datetime.datetime.strptime(record[3], "%Y-%m-%d %H:%M").date()
                        if reservation_date == current_date:  # 같은 날짜의 기록만 카운트
                            usage_count += 1
        if usage_count >= max_uses_per_day:
            print(f"하루에 최대 {max_uses_per_day}번만 좌석을 배정할 수 있습니다.")
            return True  
        return False

    def validate_recent_seat_usage(self):
        '''
        요구사항 D
        '''
        recent_reservations = []
        # max_recent_usage_day = 5       # 전역 변수로 변경
        # recent_days_for_validation = 7 # 전역 변수로 변경 

        today = datetime.datetime.strptime(recent_input_time, "%Y-%m-%d %H:%M").date()
        # print("debug : today =", today)
        with open(SEAT_ASSIGNMENT_LOG_FILE, "r") as f:
            reader = csv.reader(f)
            for record in reader:
                if record != []:
                    if record[0] == self.user.student_id and record[4] == RESERVE: # 배정 플래그 확인
                        reservation_date = datetime.datetime.strptime(record[3], "%Y-%m-%d %H:%M").date()
                        if reservation_date > today - datetime.timedelta(days = recent_days):
                            # print("debug : reservation_date =", reservation_date)
                            recent_reservations.append(reservation_date)

        # print("debug : recent_reservations = ", recent_reservations)
        recent_usage_day = len(set(recent_reservations))
        if recent_usage_day >= max_recent_usage_day:
            print("연속된 7일 기간 내에 5일을 초과하여 좌석을 배정할 수 없습니다.")
            return True
        return False

class LoginPrompt:
    '''
    로그인 프롬프트 
    '''
    def __init__(self):
         # 아래의 3개의 변수는 안 쓰이는 변수인데 삭제하는 게 나을까?
        self.current_time = None
        self.user_data = [] 
        self.admin_data = []

        self.user_prompt = UserPrompt(None, library_system) # 통합 중 수정 : 필요한 인자 추가
        self.admin_prompt = AdminPrompt(None) # 통합 중 수정 : 필요한 인자 추가

    def run(self):
        while True:
            self.input_date_time()
            library_system.check_expired_reservations(recent_input_time)
            self.process_command_input()
    
    def input_date_time(self):
        global recent_input_time

        while True:
            input_time = input("현재 시간을 입력하세요(“YYYY-MM-DD hh:mm”) > ")
            
            if re.match(TIME_SYNTAX_PATTERN, input_time) == None:
                print("잘못된 입력입니다")
                continue
            
            current_time = datetime.datetime.strptime(input_time, "%Y-%m-%d %H:%M")
            is_after_past_time = True
            with open(INPUT_TIME_FILE, "r") as f:
                reader = csv.reader(f)
                for record in reader:
                    if len(record) != 0:
                        past_time = datetime.datetime.strptime(record[0], "%Y-%m-%d %H:%M")
                        if current_time < past_time:
                            is_after_past_time = False
            
            if is_after_past_time:
                with open(INPUT_TIME_FILE, "a") as f:
                    writer = csv.writer(f)
                    writer.writerow([input_time])
                recent_input_time = input_time
                break
            else:
                print("잘못된 입력입니다")

    def display_login_prompt(self):
        print('로그인 프롬프트\n 1.사용자 회원가입\n 2.사용자 로그인\n 3.관리자 로그인\n')

    def process_command_input(self):
        while True:
            self.display_login_prompt() 
            menu = input("선택하세요 > ")
            if menu == "1":
                self.register_user()
            elif menu == "2":
                login_succeeded = self.login_user()
                if login_succeeded:
                    return
            elif menu == "3":
                login_succeeded = self.login_admin()
                if login_succeeded:
                    return

    def register_user(self):
        '''
        회원 가입
        '''
        user_id = ""
        user_name = ""
        user_password = ""
        duplicate_user = False
        have_duplicate_user = lambda existing_user, new_user : existing_user[0] == new_user[0]

        print("회원가입을 진행합니다")
        while True:
            while True:
                user_id = input("학번 9자리를 입력하세요 > ").strip()
                if re.match(USER_ID_SYNTAX_PATTERN, user_id):
                    break
            while True:
                user_name = input("이름을 입력하세요 > ").strip()
                if re.match(USER_NAME_SYNTAX_PATTERN, user_name):
                    break
            while True:
                user_password = input("비밀번호를 입력하세요 > ").strip()
                if re.match(PASSWORD_SYNTAX_PATTERN, user_password):
                    break
            
            # ** 재설계에서 모호한 점 : 처음 유저 정보를 생성할 때 마지막 로그인 시간으로 어떤 값을 넣어야할 지 고민이 필요
            new_user = [user_id, user_name, user_password, '0000-10-29 10:31']
            with open(USER_DATA_FILE, "r") as f:
                reader = csv.reader(f)
                for record in reader:
                    if len(record) == 0:
                        continue
                    if have_duplicate_user(record, new_user):
                        print("이미 가입된 회원입니다")
                        duplicate_user = True

            if duplicate_user == False:
                with open(USER_DATA_FILE, "a") as f:
                    writer = csv.writer(f)
                    writer.writerow(new_user)
                print("회원가입이 완료되었습니다")
                print()
                break

    def login_user(self):
        '''
        사용자 로그인 
        '''
        at_least_one_user_exists = False
        with open(USER_DATA_FILE, "r") as f:
            reader = csv.reader(f)
            for record in reader:
                if len(record) != 0:
                    at_least_one_user_exists = True
  
        if at_least_one_user_exists == False:
            print("가입된 이용자가 없어서 로그인 기능에 진입할 수 없습니다") 
            return False 

        user_id = ""
        user_name = ""
        user_password = ""
        login_succeeded = False
        while True:
            user_id = input("학번 9자리를 입력하세요 > ")
            if re.match(USER_ID_SYNTAX_PATTERN, user_id):
                user_id_exists = False

                with open(USER_DATA_FILE, "r") as f:
                    reader = csv.reader(f)
                    for record in reader:
                        if len(record) != 0:
                            if record[0] == user_id:
                                user_id_exists = True
    
                if user_id_exists:
                    break          

        while True:
            user_password = input("비밀번호를 입력하세요 > ")
            if re.match(PASSWORD_SYNTAX_PATTERN, user_password):
                break

        user_records = []
        with open(USER_DATA_FILE, "r") as f:
            reader = csv.reader(f)
            for record in reader:
                if len(record) != 0:
                    if record[0] == user_id and record[2] == user_password:
                        record[3] = recent_input_time
                        user_name = record[1]
                        login_succeeded = True

                user_records.append(record)

        if login_succeeded:
            with open(USER_DATA_FILE, "w") as f:
                writer = csv.writer(f)
                writer.writerows(user_records)

            library_system.user = User(user_id, user_name, user_password, recent_input_time)
            # library_system.user = User()
            print("로그인이 완료되었습니다.")
            self.user_prompt.handle_user_input()
            return True
        
        return False

    def login_admin(self):
        '''
        관리자 로그인 함수
        '''
        admin_id = ""
        admin_password = ""
        login_succeeded = False

        print("관리자 로그인")
        while True:
            admin_id = input("ID 입력 > ")
            if re.match(ADMIN_ID_SYNTAX_PATTERN, admin_id):
                admin_id_exists = False

                with open(ADMIN_DATA_FILE, "r") as f:
                    reader = csv.reader(f)
                    for record in reader:
                        if len(record) != 0:
                            if record[0] == admin_id:
                                admin_id_exists = True
    
                if admin_id_exists:
                    break          

        while True:
            admin_password = input("PW 입력 > ")
            if re.match(PASSWORD_SYNTAX_PATTERN, admin_password):
                break

        admin_records = []
        with open(ADMIN_DATA_FILE, "r") as f:
            reader = csv.reader(f)
            for record in reader:
                if len(record) != 0:
                    if record[0] == admin_id and record[1] == admin_password: ## 함수로 변경하는 것이 나을까?
                        login_succeeded = True

                admin_records.append(record)

        if login_succeeded:
            self.admin_prompt.admin = Admin(admin_id)
            # self.admin_prompt.admin = Admin()
            self.admin_prompt.handle_admin_input()
            return True
        
        return False

class UserPrompt:

    #생성자
    def __init__(self, user, library_system):
        self.user = user
        self.library_system = library_system 

    def display_user_menu(self):
        print("사용자용 프롬프트")
        print("1. 도서관 좌석 조회\n2. 좌석 배정\n3. 좌석 반납\n4. 사용자 로그아웃(종료)")

    def handle_user_input(self):
        # 올바른 입력이 처리될 때까지 무한반복
        while True:
            self.display_user_menu()
            choice = input("선택하세요 > ")

            if choice in ["1", "2", "3", "4"]:
                if choice == "1":
                    self.library_system.show_seat_status()
                elif choice == "2":
                    self.library_system.reserve_seat()
                elif choice == "3":
                    self.library_system.cancel_reservation()
                elif choice == "4":
                    if self.logout_user():
                        print("로그아웃이 완료되었습니다.")
                        return
                    else:
                        continue  
            # 1,2,3,4 외의 입력이 들어왔을 때
            else:
                continue


    def logout_user(self):
        while True:
            confirm = input("로그아웃 하시겠습니까?(Y/N) > ")
            if confirm in ["Y", "N"]:
                if confirm == "Y":
                    return True
                else: return False
            else:
                continue

class AdminPrompt:
    def __init__(self, admin):
        self.admin = admin

    def display_admin_menu(self):
        """관리자 메뉴를 출력하는 함수"""

        # print("debug : ")
        # library_system.user = User("", "", "")
        # library_system.show_seat_status()

        print("관리자용 프롬프트")
        print("1. 좌석 추가")
        print("2. 좌석 삭제")
        print("3. 열람실 추가")
        print("4. 열람실 삭제")
        print("5. 열람실 최대 좌석 수 변경")
        print("6. 관리자 로그아웃(종료)")


    def handle_admin_input(self):
        """관리자 입력을 처리하는 함수"""
        while True:
            self.display_admin_menu()
            admin_input = input("선택하세요 > ")

            # 입력이 1, 2, 3, 4, 5, 6으로만 구성되어 있는지 확인 (공백 및 기타 문자 허용 안함)
            if admin_input in ["1", "2", "3", "4", "5", "6"]:
                choice = int(admin_input)
                if choice == 1:
                    self.admin.add_seats()  # 좌석 추가 기능
                elif choice == 2:
                    self.admin.remove_seats()  # 좌석 삭제 기능
                elif choice == 3:
                    self.admin.add_reading_room()  # 열람실 추가 기능
                elif choice == 4:
                    self.admin.remove_reading_room()  # 열람실 삭제 기능
                elif choice == 5:
                    self.admin.change_reading_room_limit()  # 최대 좌석 수 변경
                elif choice == 6:
                    logout_selected = self.logout_admin()  # 로그아웃 처리
                    if logout_selected:
                        break  # while 루프 종료

            else:
                # 오류 메시지 없이 다시 관리자 메뉴로 돌아감
                continue

    def logout_admin(self):
        """관리자 로그아웃 처리"""
        input_value = None  # 로그아웃 여부 저장하는 변수
        print("관리자 로그아웃(종료)")
        while True:
            input_value = input("로그아웃 하시겠습니까?(Y/N) > ")

            if input_value == "Y":
                print("로그아웃이 완료되었습니다.")
                # 현재 시간을 자동으로 기록
                return True  # 로그아웃 여부 리턴

            elif input_value == "N":
                return False  # 관리자 프롬프트로 복귀


            else:
                # 오류 처리: 아무 메시지도 출력하지 않고 다시 입력 받음
                continue

class FileValidator:
    '''
    파일 무결성 검증 객체
    '''
    def validate_admin_data_file(self, check_record_syntax, check_meaning):
        '''
        관리자 정보 파일 검증 메소드
        '''
        # 작업 디렉토리에 파일이 존재하지 않는다면
        if not os.path.exists(ADMIN_DATA_FILE):
            print(f"WARN : {ADMIN_DATA_FILE} 파일이 존재하지 않습니다.")
            try:
                print(f"새로운 {ADMIN_DATA_FILE}파일을 생성합니다...")
                print("기본 관리자 계정을 생성합니다...")
                # 파일을 생성하고 기본 관리자 계정을 추가
                with open(ADMIN_DATA_FILE, "w") as f:
                    writer = csv.writer(f)
                    writer.writerow(["defaultadmin", "12345678"])
            except:
                # 생성 중 예외 발생 시 종료
                print(f"ERROR : 새로운 {ADMIN_DATA_FILE} 파일 생성에 실패했습니다!!! 프로그램을 종료합니다")
                sys.exit()
            return
        
        with open(ADMIN_DATA_FILE, "r") as f:
            reader = csv.reader(f)

            records = []
            for record in reader:
                if len(record) != 0: # 빈 레코드가 아니면
                    
                    if check_record_syntax(record) == False: # 문법규칙을 위배하면
                        print(f"ERROR : {ADMIN_DATA_FILE} 파일에 규칙에 맞지 않는 레코드가 존재합니다!!! 프로그램을 종료합니다")
                        sys.exit()

                    records.append(record)

        if len(records) == 0:  # 파일에 레코드가 하나도 없으면 
            print(f"ERROR : {ADMIN_DATA_FILE} 파일에 레코드가 없습니다!!! 프로그램을 종료합니다")
            sys.exit()

        if check_meaning(records) == False: # 의미규칙과 맞지 않으면
            print(f"ERROR: {ADMIN_DATA_FILE} 파일에 규칙에 맞지 않는 레코드가 존재합니다!!! 프로그램을 종료합니다")
            sys.exit()

    def validate_user_data_file(self, check_record_syntax):
        '''
        사용자 정보 파일 검증 메소드
        '''
        if not os.path.exists(USER_DATA_FILE):   # 작업 디렉토리에 파일이 존재하지 않는다면
            print(f"WARN : {USER_DATA_FILE} 파일이 존재하지 않습니다")
            print(f"새로운 사용자 정보 파일 {USER_DATA_FILE}을 생성합니다...")
            try:
                # 파일 생성
                open(USER_DATA_FILE, "w")
            except:
                # 생성 중 예외 발생 시 종료
                print(f"ERROR : 새로운 {USER_DATA_FILE} 파일 생성에 실패했습니다!!! 프로그램을 종료합니다")
                sys.exit()    
            return
        
        with open(USER_DATA_FILE, "r") as f:
            reader = csv.reader(f)
            
            for record in reader:
                if len(record) != 0: # 빈 레코드가 아니면
                    if check_record_syntax(record) == False: # 문법 규칙에 맞지 않으면
                        print(f"ERROR : {USER_DATA_FILE} 파일에 규칙에 맞지 않는 레코드가 존재합니다!!! 프로그램을 종료합니다")
                        sys.exit() 
    
    def validate_input_time_file(self, check_record_syntax):
        '''
        입력 시간 파일 검증 메소드
        '''
        if not os.path.exists(INPUT_TIME_FILE): # 작업 디렉토리에 파일이 존재하지 않는다면
            print(f"WARN : {INPUT_TIME_FILE} 파일이 존재하지 않습니다")
            print(f"새로운 입력 시간 파일 {INPUT_TIME_FILE}을 생성합니다...")
            try:
                 # 파일 생성
                open(INPUT_TIME_FILE, "w")
            except:
                # 생성 중 예외 발생 시 종료
                print(f"ERROR : {INPUT_TIME_FILE} 파일 생성에 실패했습니다!!! 프로그램을 종료합니다")
                sys.exit()
            return
        
        with open(INPUT_TIME_FILE, "r") as f:
            reader = csv.reader(f)
            
            for record in reader:
                if len(record) != 0: # 빈 레코드가 아니면
                    if check_record_syntax(record) == False: # 문법 규칙에 맞지 않으면
                        print(f"ERROR : {INPUT_TIME_FILE} 파일에 규칙에 맞지 않는 레코드가 존재합니다!!! 프로그램을 종료합니다")
                        sys.exit()

    def validate_seat_data_file(self, check_record_syntax):
        '''
        좌석 정보 파일 검증 메소드
        '''
        if not os.path.exists(SEAT_DATA_FILE):
            print(f"WARN : {SEAT_DATA_FILE} 파일이 존재하지 않습니다")
            print(f"새로운 좌석 정보 파일 {SEAT_DATA_FILE}을 생성합니다...")
            try:
                with open(SEAT_DATA_FILE, "w") as f:
                    writer = csv.writer(f)
                    for seat_number in range(1, 51): # 중간 발표용 제출 후 수정
                        writer.writerow([seat_number, 1, 'O', '0000-10-29 10:31', '201000000'])
            except:
                print(f"ERROR : 새로운 {SEAT_DATA_FILE} 파일 생성에 실패했습니다!!! 프로그램을 종료합니다")
                sys.exit()
            return 
       
        with open(SEAT_DATA_FILE, "r") as f:
            reader = csv.reader(f)
            
            for record in reader:
                if len(record) != 0:
                    if check_record_syntax(record) == False:
                        print(f"ERROR : {SEAT_DATA_FILE} 파일에 규칙에 맞지 않는 레코드가 존재합니다!!! 프로그램을 종료합니다")
                        sys.exit()
       
    def validate_seat_assignment_log_file(self, check_record_syntax):
        '''
        좌석 배정 기록 파일 검증 메소드
        '''
        if not os.path.exists(SEAT_ASSIGNMENT_LOG_FILE):
            print(f"WARN : {SEAT_ASSIGNMENT_LOG_FILE} 파일이 존재하지 않습니다")
            print(f"{SEAT_ASSIGNMENT_LOG_FILE} 파일을 생성합니다...")
            try:
                open(SEAT_ASSIGNMENT_LOG_FILE, "w")
            except:
                print(f"ERROR : {SEAT_ASSIGNMENT_LOG_FILE} 파일 생성에 실패했습니다!!! 프로그램을 종료합니다")
                sys.exit()
            return
        
        with open(SEAT_ASSIGNMENT_LOG_FILE, "r") as f:
            reader = csv.reader(f)  
            for record in reader:
                if len(record) != 0:
                    if check_record_syntax(record) == False:
                        print(f"{SEAT_ASSIGNMENT_LOG_FILE} 파일에 규칙에 맞지 않은 레코드가 존재합니다")
                        sys.exit()

    def validate_reading_room_data_file(self, check_record_syntax):
        '''
        열람실 정보 파일 검증 메소드
        '''
        if not os.path.exists(READING_ROOM_DATA_FILE):
            print(f"WARN : {READING_ROOM_DATA_FILE} 파일이 존재하지 않습니다")
            print(f"새로운 열람실 정보 파일 {READING_ROOM_DATA_FILE}을 생성합니다...")
            try:
                with open(READING_ROOM_DATA_FILE, "w") as f:
                    writer = csv.writer(f)
                    writer.writerow([1, 100])
            except:
                print(f"ERROR : 새로운 {READING_ROOM_DATA_FILE} 파일 생성에 실패했습니다!!! 프로그램을 종료합니다")
                sys.exit()
            return
        
        record_count = 0 
        with open(READING_ROOM_DATA_FILE, "r") as f:
            reader = csv.reader(f)
            
            for record in reader:
                if len(record) == 0:
                    continue

                # print(record)
                if check_record_syntax(record) == False:
                    print(f"{READING_ROOM_DATA_FILE} 파일에 규칙에 맞지 않은 레코드가 존재합니다")
                    sys.exit()

                record_count += 1
        
        # if record_count != 1:
        #     print(f"ERROR : {READING_ROOM_DATA_FILE}파일에 두 개 이상의 레코드가 존재합니다!!! 프로그램을 종료합니다.")
        #     sys.exit()

    def validate_all_files(self):
        check_user_data_syntax = lambda record : True if (re.match(USER_ID_SYNTAX_PATTERN, record[0].strip()) and re.match(USER_NAME_SYNTAX_PATTERN, record[1].strip()) and re.match(PASSWORD_SYNTAX_PATTERN, record[2].strip()) and re.match(TIME_SYNTAX_PATTERN, record[3].strip())) else False # 사용자 마지막 로그인 시간이 필요한가?
        check_input_time_syntax = lambda record : True if re.match(TIME_SYNTAX_PATTERN, record[0].strip()) else False
        check_seat_data_syntax = lambda record : True if re.match(SEAT_NUMBER_SYNTAX_PATTERN, record[0].strip()) and re.match(READING_ROOM_NUMBER_SYNTAX_PATTERN, record[1].strip()) and re.match(SEAT_STATUS_SYNTAX_PATTERN, record[2].strip()) and re.match(TIME_SYNTAX_PATTERN, record[3].strip()) and re.match(USER_ID_SYNTAX_PATTERN, record[4].strip()) else False
        check_seat_assignment_log_syntax = lambda record : True if (len(record) == 5 and re.match(USER_ID_SYNTAX_PATTERN, record[0].strip()) and re.match(SEAT_NUMBER_SYNTAX_PATTERN, record[1].strip()) and re.match(READING_ROOM_NUMBER_SYNTAX_PATTERN, record[2].strip()) and re.match(TIME_SYNTAX_PATTERN, record[3].strip()) and re.match(ASSIGNMENT_LOG_RECORD_TYPE_SYNTAX_PATTERN, record[4].strip())) else False
        check_reading_room_data_syntax = lambda record : True if re.match(READING_ROOM_NUMBER_SYNTAX_PATTERN, record[0].strip()) and re.match(READING_ROOM_SEAT_LIMIT_SYNTAX_PATTERN, record[1].strip()) else False
        
        self.validate_admin_data_file(check_admin_data_syntax, check_admin_data_meaning)
        self.validate_user_data_file(check_user_data_syntax)
        self.validate_input_time_file(check_input_time_syntax)
        self.validate_seat_data_file(check_seat_data_syntax)
        self.validate_seat_assignment_log_file(check_seat_assignment_log_syntax) # 배정 플래그 검증
        self.validate_reading_room_data_file(check_reading_room_data_syntax)

'''
전역함수
'''
def check_admin_data_syntax(record):
    # 관리자 정보 파일의 레코드가 문법 규칙을 만족하면 True를 반환하고, 그렇지 않으면 False를 반환
    return True if (re.match(ADMIN_ID_SYNTAX_PATTERN, record[0].strip()) and re.match(PASSWORD_SYNTAX_PATTERN, record[1].strip())) else False

def check_admin_data_meaning(records):
    # records에 있는 모든 레코드가 관리자 정보 파일의 문법규칙을 만족하면 True를 반환, 그렇지 않으면 False를 반환
    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            if records[i][0] == records[j][0]:
                return False
    return True

def load_reading_room_data(record_to_entity = lambda x : [int(x[0]), int(x[1])]):
    with open(READING_ROOM_DATA_FILE, "r") as f:
        reader = csv.reader(f)
        for record in reader:
            if len(record) != 0: # csv 파일에서 빈줄이 아니라면  
                entity = record_to_entity(record) # 레코드를 딕셔너리로 변환
                reading_room_list.append(entity)

    # print("debug :", reading_room_list)

def main():
    global library_system

    file_validator = FileValidator()
    file_validator.validate_all_files()
    load_reading_room_data()
    
    library_system = LibrarySystem()
    login_prompt = LoginPrompt()
    login_prompt.run()

if __name__ == "__main__":
    main()
