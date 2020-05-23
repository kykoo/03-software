import time
import array
import os
import uerrno
import pycom
import struct

def today():
    return (time.time()//(3600*24))*(3600*24)

def yesterday():
    return (time.time()//(3600*24)-1)*(3600*24)


def zeros(n,m):
    y = [array.array('f',[0 for j in range(m)]) for i in range(n)]
    return y

def mean(U):
    n = len(U)
    m = len(U[0])
    Usum = [0.0 for i in range(n)]
    for i in range(n):
        for j in range(m):
            Usum[i] += U[i][j]
    Uavg = [Usum[i]/m for i in range(n)]
    return Uavg

def matrix_plus_row(x,y):
    n = len(x)
    m = len(x[0])
    for i in range(n):
        for j in range(m):
            x[i][j] = x[i][j] + y[i]
    return

def matrix_minus_row(x,y):
    n = len(x)
    m = len(x[0])
    for i in range(n):
        for j in range(m):
            x[i][j] = x[i][j] - y[i]
    return

def rmsd(x):
    n = len(x)
    m = len(x[0])
    x_mean = mean(x)
    matrix_minus_row(x, x_mean)
    y_sum = [0.0 for i in range(n)]
    for i in range(n):
        for j in range(m):
            y_sum[i] += x[i][j]**2.0
    matrix_plus_row(x, x_mean)
    y = [(y_sum[i]/m)**0.5 for i in range(n)]
    return y

def decimate(x, y, nfactor):
    # COEFFICIENTS generated from
    #   nfilter = 8
    #   b, a = cheby1(n_filter, 0.05, 0.8 / n)
    n_filter = 8
    a = [0.0 for i in range(n_filter+1)]
    b = [0.0 for i in range(n_filter+1)]
    if nfactor == 4:
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
        print('nfactor={} not implemented yet'.format(nfactor))

    n = len(x)
    m = len(x[0])

    x_mean = mean(x)
    matrix_minus_row(x, x_mean) 
    for i in range(n):
        d_prev = array.array('f',[0.0 for i in range(n_filter)])
        d_now  = array.array('f',[0.0 for i in range(n_filter)])
        for j in range(m):
            y[i][j] = b[0]*x[i][j] + d_prev[0]
            for k in range(n_filter):
                d_now[k] =  b[k+1]*x[i][j] - a[k+1]*y[i][j] + d_prev[k+1] if k < n_filter-1 else \
                            b[k+1]*x[i][j] - a[k+1]*y[i][j]
            d_prev = list(d_now)
    matrix_plus_row(x, x_mean)
    matrix_plus_row(y, x_mean)

    # yd = [y[n*i] for i in range(int(N/n))]
    # print('**** y ***************')
    # for i in range(10):
    #     # print('{:.20f}, {:.20f}'.format(acc[i][0], y[i][0]))
    #     print('{:.20f}, {:.20f}, {:.20f}'.format(y[i][0], y[i][1], y[i][2]))
    # print('**** yd ***************')
    # for i in range(10):
    #     # print('{:.20f}, {:.20f}'.format(acc[i][0], y[i][0]))
    #     print('{:.20f}, {:.20f}, {:.20f}'.format(yd[i][0], yd[i][1], yd[i][2]))
    # return yd


# def rms(U):
#     Ussum = 0.0
#     count  = 0
#     Uavg = avg(U)
#     for u in U:
#         Ussum += (u-Uavg)**2.0
#         count += 1
#     Urms = (Ussum/count)**0.5
#     return Urms

def datetime_string(time_sec):
    t_ = time.localtime(time_sec)
    return '{}-{:0>2d}{:0>2d}-{:0>2d}{:0>2d}{:0>2d}'.format(t_[0],t_[1],t_[2],t_[3],t_[4],t_[5])

def date_string(time_sec):
    t_ = time.localtime(time_sec)
    return '{}-{:0>2d}{:0>2d}'.format(t_[0],t_[1],t_[2])

def year_string(time_sec):
    t_ = time.localtime(time_sec)
    return '{}'.format(t_[0])

def mkdir(path):
    try:
        cwd = os.getcwd()
        os.chdir(path)
        os.chdir(cwd)
        return False
    except OSError as exc:
        if exc.args[0] == uerrno.ENOENT:
            os.mkdir(path)
            return False
        else:
            raise
    except:
        raise

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
