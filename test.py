from itertools import chain

username = "test"
phone = "9174034023, 9176053429, 9176053407"
numbers = phone.split(',')
numbers = [x.strip() for x in numbers]
num_count = len(numbers)
inserts = ", ".join(["(%s, %s)"]*num_count)
query = 'INSERT INTO PhoneNumbers (username, phone_num) VALUES ' + inserts
inputs = tuple(chain.from_iterable(zip([username]*num_count, numbers)))

print(f"query: {query}\ninputs: {inputs}")