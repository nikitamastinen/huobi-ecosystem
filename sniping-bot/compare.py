with open("after.txt") as after:
    with open("before.txt") as before:
        a = []
        b = []
        for i in after:
            a.append([j for j in i.split()])
        for j in before:
            b.append([j for j in j.split()])

        total = 0
        for i in range(len(a)):
            if a[i][1] != b[i][1]:
                print(a[i][0] + ": ", b[i][1], "->", a[i][1], "Прибыль: ", (float(a[i][1]) - float(b[i][1])))
                total += (float(a[i][1]) - float(b[i][1]))
        print("Общая прибыль: ", total)

