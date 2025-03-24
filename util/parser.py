import re


class Parser:

    def hrsFormatter(arr):
        if arr == "":
            return 0

        else:
            arr = arr.split(":")
            stack = [float(i) for i in arr]

            if stack[1] == 15:
                stack[1] = .25
            elif stack[1] == 30:
                stack[1] = .50
            elif stack[1] == 45:
                stack[1] = .75

            return stack[0] + stack[1]

    def xlsParser(sheet,
                  mincolx, minrowy,
                  maxcolx, maxrowy,
                  target, xbuff) -> []:
        answer = []

        for i in range(minrowy, maxrowy):
            for j in range(mincolx, maxcolx):
                curr = sheet.cell_value(i, j)
                if xbuff is not None:
                    if re.search(pattern=target, string=curr) is not None:
                        j += xbuff
                        answer.append(sheet.cell_value(i, j))
                        answer.append([i, j])
                else:
                    if re.search(pattern=target, string=curr) is not None:
                        answer.append(curr)
                        answer.append([i, j])
        return answer
