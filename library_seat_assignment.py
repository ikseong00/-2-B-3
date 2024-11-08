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

ADMIN_DATA_FILE = "libary_admin_data.csv" 
USER_DATA_FILE = "libary_user_data.csv"
SEAT_DATA_FILE = "library_seat_data.csv"
INPUT_TIME_FILE = "library_input_time_data.csv"
SEAT_ASSIGNMENT_LOG_FILE = "library_seat_assignment_log.csv"
READING_ROOM_DATA_FILE = "library_reading_room_data.csv"

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
    def __init__(self): # ** 
        self.id = "defaultadmin"  # 관리자 아이디

    def add_seats(self):
        """좌석 추가 함수"""
        print("좌석 추가")
        while True:
            # 확장을 대비해 입력받은 값을 리스트에 추가하는 방식으로 구현
            seats_numbers = []  # 확장 대비를 위한 리스트
            add_seat_number = input("추가할 좌석 번호 입력 > ")
            seats_numbers.append(add_seat_number)  # 입력 받은 좌석 번호를 리스트에 추가
            if re.match(SEAT_NUMBER_SYNTAX_PATTERN, add_seat_number) != None:
                add_seat_number = int(add_seat_number)
    
                if not library_system.max_seat_detect(1):
                    return  # 관리자 프롬프트로 돌아감

                now_seats = library_system.get_seats()

                # 이미 존재하는 좌석 번호 중 상태가 'D'인 좌석을 찾아서 상태를 변경
                seat_to_restore = next((seat for seat in now_seats if seat[0] == add_seat_number and seat[2] == "D"), None)
                if seat_to_restore:
                    seat_to_restore[2] = "O"  # 상태를 'O'로 변경
                    seat_to_restore[3] = '0000-10-29 10:31'
                    seat_to_restore[4] = '201000000'
                    library_system.save_seat_data()
                    break
                elif any(seat[0] == add_seat_number and seat[2] != "D" for seat in now_seats):
                    continue  # 다시 입력 받음

                else:
                    now_seats.append([add_seat_number, 1, "O", '0000-10-29 10:31', '201000000'])

                    library_system.seats = now_seats
                    library_system.save_seat_data()  # 좌석 데이터 저장
                    break
            else:
                # 오류 처리: 아무 메시지도 출력하지 않고 다시 입력 받음
                continue

    def remove_seats(self):
        """좌석 삭제 함수"""
        print("좌석 삭제")
        while True:
            # 사용 가능한 좌석이 1개 이하인지 확인
            available_seats = [seat for seat in library_system.get_seats() if seat[2] == "O"]
            if len(available_seats) <= 1:
                print("더 이상 좌석을 삭제할 수 없습니다.")
                return  # 관리자 프롬프트로 돌아감
            
            # 확장을 대비해 입력받은 값을 리스트에 추가하는 방식으로 구현
            seats_numbers = []  # 확장 대비를 위한 리스트
            remove_seat_number = input("삭제할 좌석 번호 입력 > ")
            seats_numbers.append(remove_seat_number)  # 입력 받은 좌석 번호를 리스트에 추가
            if re.match(SEAT_NUMBER_SYNTAX_PATTERN, remove_seat_number) != None:
                remove_seat_number = int(remove_seat_number)
                now_seats = library_system.get_seats()

                # 좌석 번호가 존재하는지 확인
                seat = next((s for s in now_seats if s[0] == remove_seat_number), None)
                if seat:
                    if seat[2] == "O":
                        seat[2] = "D"  # 상태를 빈 공간으로 변경하여 결번 처리
                        library_system.seats = now_seats
                        library_system.save_seat_data()  # 좌석 데이터 저장
                        print(f"{remove_seat_number}번 좌석 삭제가 완료되었습니다.")
                        break
                else:
                    continue
            else:
                # 오류 처리: 아무 메시지도 출력하지 않고 다시 입력 받음
                continue

# def print_aligned_seat_status(seats, user_id, row_length = 10):  # 좌석 상태 출력 형태를 조정 (1줄에 10개씩 표시)
#     seat_count = 0
#     seat_status_row = ""
    
#     for seat in seats:
#         seat_count += 1
        
#         # 로그인 중인 사용자가 이용 중인 좌석이면 ★로 표시
#         if seat[2] == "D" :
#             seat_count -= 1
#             continue
        
#         if seat[4] == user_id:
#             seat_status_row += f"{seat[0]:2}: [★]   "
#         else:
#             seat_status_row += f"{seat[0]:2}: [{seat[2]}]   "
        
#         if seat_count % row_length == 0:
#             seat_status_row += "\n"
        
#     print(seat_status_row)

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

    def show_seat_status(self, room_number = 1, show_status_mode = "default"):
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
                
                if seat[4] == self.user.student_id:
                    seat_status += f"{seat[0]:2}: [★]   "
                else:
                    seat_status += f"{seat[0]:2}: [{seat[2]}]   "
                
                if seat_count % STATUS_ROW_LENGTH == 0:
                    seat_status += "\n"
                
            print(seat_status)
            
    def reserve_seat(self):
        if self.check_four_day_consecutive_usage():
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
                            writer.writerow([self.user.student_id, seat_number, seat[1], recent_input_time])
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
                    if record[0] == self.user.student_id:
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
                print("과거의 시간을 입력할 수 없습니다. 다시 입력해주세요")
                # print("debug : 과거의 시간을 입력할 수 없습니다")

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
            #self.admin_prompt.admin = Admin(admin_id)
            self.admin_prompt.admin = Admin()
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
        print("3. 관리자 로그아웃(종료)")

    def handle_admin_input(self):
        """관리자 입력을 처리하는 함수"""
        while True:
            self.display_admin_menu()
            admin_input = input("선택하세요 > ")

            # 입력이 1, 2, 3으로만 구성되어 있는지 확인 (공백 및 기타 문자 허용 안함)
            if admin_input in ["1", "2", "3"]:
                choice = int(admin_input)
                if choice == 1:
                    self.admin.add_seats()  # 좌석 추가 기능
                elif choice == 2:
                    self.admin.remove_seats()  # 좌석 삭제 기능
                elif choice == 3:
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
                    for seat_number in range(1, 51):
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
        
        if record_count != 1:
            print(f"ERROR : {READING_ROOM_DATA_FILE}파일에 두 개 이상의 레코드가 존재합니다!!! 프로그램을 종료합니다.")
            sys.exit()

    def validate_all_files(self):
        check_user_data_syntax = lambda record : True if (re.match(USER_ID_SYNTAX_PATTERN, record[0].strip()) and re.match(USER_NAME_SYNTAX_PATTERN, record[1].strip()) and re.match(PASSWORD_SYNTAX_PATTERN, record[2].strip()) and re.match(TIME_SYNTAX_PATTERN, record[3].strip())) else False # 사용자 마지막 로그인 시간이 필요한가?
        check_input_time_syntax = lambda record : True if re.match(TIME_SYNTAX_PATTERN, record[0].strip()) else False
        check_seat_data_syntax = lambda record : True if (re.match(SEAT_NUMBER_SYNTAX_PATTERN, record[0].strip()) and re.match(READING_ROOM_NUMBER_SYNTAX_PATTERN, record[1].strip()) and re.match(SEAT_STATUS_SYNTAX_PATTERN, record[2].strip()) and re.match(TIME_SYNTAX_PATTERN, record[3].strip()) and re.match(USER_ID_SYNTAX_PATTERN, record[4].strip())) else False
        check_seat_assignment_log_syntax = lambda record : True if (re.match(USER_ID_SYNTAX_PATTERN, record[0].strip()) and re.match(SEAT_NUMBER_SYNTAX_PATTERN, record[1].strip()) and re.match(READING_ROOM_NUMBER_SYNTAX_PATTERN, record[2].strip()) and re.match(TIME_SYNTAX_PATTERN, record[3].strip())) else False
        check_reading_room_data_syntax = lambda record : True if re.match(READING_ROOM_NUMBER_SYNTAX_PATTERN, record[0].strip()) and re.match(READING_ROOM_SEAT_LIMIT_SYNTAX_PATTERN, record[1].strip()) else False
        
        self.validate_admin_data_file(check_admin_data_syntax, check_admin_data_meaning)
        self.validate_user_data_file(check_user_data_syntax)
        self.validate_input_time_file(check_input_time_syntax)
        self.validate_seat_data_file(check_seat_data_syntax)
        self.validate_seat_assignment_log_file(check_seat_assignment_log_syntax)
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
