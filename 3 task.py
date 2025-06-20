import re

def main(): 
    # Читаем файл и разделяем его на строки
    with open('openssh.log', 'r', encoding='UTF-8') as f_obj:
        log = f_obj.read()

    s_log = log.split('\n')
    
    # Если строка содержит 'Failed password for root from
    failed_pass = {}
    for sub_str in s_log:
        if 'Failed password for root from' in sub_str: 
            ip = re.search('([0-9]{1,3}[\\.]){3}[0-9]{1,3}', sub_str) # Находим ip адреса в строке
            ip_str = ip.group()

            # Сохраняем в словарь
            if ip_str in failed_pass.keys():
                failed_pass[ip_str] = failed_pass[ip_str] + 1
            else:
                failed_pass[ip_str] = 1

    

    print(failed_pass)



if __name__ == '__main__':
    main()   