import time
import array


def decimate(x, n):
    # COEFFICIENTS generated from
    #   nfilter = 8
    #   b, a = cheby1(n_filter, 0.05, 0.8 / n)
    n_filter = 8
    a = [0.0 for i in range(n_filter+1)]
    b = [0.0 for i in range(n_filter+1)]
    if n == 4:
        a[0]=1.0000000000000000000000000000000000000000000000000000000000000000000000
        a[1]=-6.0971129583714169797303839004598557949066162109375000000000000000000000
        a[2]=16.9346004760360564489474199945107102394104003906250000000000000000000000
        a[3]=-27.8660382719920320937490032520145177841186523437500000000000000000000000
        a[4]=29.6304537334959903205344744492322206497192382812500000000000000000000000
        a[5]=-20.8090923187866643218058015918359160423278808593750000000000000000000000
        a[6]=9.4142790899313375518886459758505225181579589843750000000000000000000000
        a[7]=-2.5067378070648831389632960053859278559684753417968750000000000000000000
        a[8]=0.3006872193662448733419978452729992568492889404296875000000000000000000
        b[0]=0.0000040359292893478158925114895883012877675355412065982818603515625000
        b[1]=0.0000322874343147825271400919167064103021402843296527862548828125000000
        b[2]=0.0001130060201017388449903217084724360574909951537847518920898437500000
        b[3]=0.0002260120402034776899806434169448721149819903075695037841796875000000
        b[4]=0.0002825150502543471260283314272498955688206478953361511230468750000000
        b[5]=0.0002260120402034776899806434169448721149819903075695037841796875000000
        b[6]=0.0001130060201017388449903217084724360574909951537847518920898437500000
        b[7]=0.0000322874343147825271400919167064103021402843296527862548828125000000
        b[8]=0.0000040359292893478158925114895883012877675355412065982818603515625000
    else:
        print('not implemented yet')

    m = 3
    d_prev = zeros(n_filter,m)
    d_now = zeros(n_filter,m)
    N = len(x)
    # x_mean = mean(x)
    # print('x_mean={}'.format(x_mean))
    # x = matrix_minus_row(x, x_mean)
    # x_mean = mean(x)
    # print('x_mean={}'.format(x_mean))
    y = zeros(N,m)
    for i in range(N):
        for j in range(m):
            y[i][j] = b[0]*x[i][j] + d_prev[0][j]
        for k in range(n_filter):
            for j in range(m):
                d_now[k][j]= b[k+1]*x[i][j] - a[k+1]*y[i][j] + d_prev[k+1][j] if k < n_filter-1 else \
                             b[k+1]*x[i][j] - a[k+1]*y[i][j]
        d_prev = d_now
        print('{}, {}'.format(x[i][0], y[i][0]))
    # y = matrix_plus_row(y, x_mean)
    yd = [y[4*i] for i in range(int(N/4))]

    return yd

def matrix_plus_row(x,y):
    n = len(x)
    m = len(x[0])
    z = zeros(n,m)
    for i in range(len(x)):
        for j in range(len(y)):
            z[i][j] = x[i][j] + y[j]
    return z

def matrix_minus_row(x,y):
    n = len(x)
    m = len(x[0])
    z = zeros(n,m)
    for i in range(len(x)):
        for j in range(len(y)):
            z[i][j] = x[i][j] - y[j]
    return z

def zeros(n,m):
    y = []
    for i in range(n):
        y.append(array.array('f',[0 for i in range(m)]))
    return y

def rmsd(x):
    n = len(x)
    m = len(x[0])
    x_mean = mean(x)
    dx = matrix_minus_row(x, x_mean)
    y_sum = [0.0 for i in range(m)]
    for dx_ in dx:
        for j in range(m):
            y_sum[j] += dx_[j]**2.0
    y = [(y_sum[j]/n)**0.5 for j in range(m)]
    return y

def mean(U):
    n = len(U)
    m = len(U[0])
    Usum = [0.0 for i in range(m)]
    for u in U:
        for j in range(m):
            Usum[j] += u[j]
    Uavg = [Usum[j]/n for j in range(m)]
    return Uavg

def rms(U):
    Ussum = 0.0
    count  = 0
    Uavg = avg(U)
    for u in U:
        Ussum += (u-Uavg)**2.0
        count += 1
    Urms = (Ussum/count)**0.5
    return Urms

def datetime_string(time_sec):
    t_ = time.localtime(time_sec)
    return '{}-{:0>2d}{:0>2d}-{:0>2d}{:0>2d}{:0>2d}'.format(t_[0],t_[1],t_[2],t_[3],t_[4],t_[5])

def date_string(time_sec):
    t_ = time.localtime(time_sec)
    return '{}-{:0>2d}{:0>2d}'.format(t_[0],t_[1],t_[2])

def getNextGridTime(T_now,T_exec):
    res = T_now%T_exec
    if res != 0:
        T_start = T_now - res + T_exec
    else:
        T_start = T_now
    return T_start

def waitUntil(T_start):
    while True:
        if time.time() >= T_start:
            break
    return
