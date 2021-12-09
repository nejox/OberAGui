DATA_FILEPATH = "data/data.csv"
def generateData():
    from numpy.random import seed
    from numpy.random import randint
    seed(1)
    products = ['A', 'B', 'C', 'D']
    oldKey = 0
    data = []
    for i in range(0,100):
        key = 0
        while True:
            key = randint(0,4)
            if key != oldKey:
                oldKey = key
                break
        currentProd = products[key]
        value = randint(15,60)
        timestmp = datetime.now(tz=None).strftime("%d-%b-%Y %H:%M:%S")
        data.extend([(currentProd,value,timestmp)])
    df = pd.DataFrame(data,columns=["Material","Duration","Timestamp"])
    df.to_csv(DATA_FILEPATH, sep=";",index=False)
    return df