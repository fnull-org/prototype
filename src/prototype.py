from utils import get_local_ip
from random_code import gen_random_code

if __name__ == "__main__":
    ip_address = get_local_ip()
    code = gen_random_code()
    print(code)