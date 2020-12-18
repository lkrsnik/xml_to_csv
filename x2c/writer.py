import csv


def write_csv(path, out_list, commands):
    if len(out_list) == 0:
        return
    with open(path, 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter='\t',
                                quotechar='"')
        writer.writerow([k for k in commands.keys()])
        for line in out_list:
            writer.writerow(line)
