
fun_pointer = 'main.f1'

def f2():
    d = 0
    while True:
        print(d)
        fun_pointer()
        time.sleep(1)
        d += 1
