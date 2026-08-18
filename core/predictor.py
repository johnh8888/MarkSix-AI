def predict_v10(history, lottery_name="六合彩"):


    from collections import Counter


    nums=[]


    for row in history:


        # -----------------------
        # list格式
        # -----------------------

        if isinstance(row,list):

            nums.extend(

                [
                    x for x in row
                    if isinstance(x,int)
                    and 1<=x<=49
                ]

            )



        # -----------------------
        # dict格式
        # -----------------------

        elif isinstance(row,dict):


            # 新版字段

            if "numbers" in row:


                nums.extend(

                    [

                    int(x)

                    for x in row["numbers"]

                    if 1<=int(x)<=49

                    ]

                )



            else:


                # 兼容SQLite字段

                for k,v in row.items():


                    if isinstance(v,int):


                        if 1<=v<=49:

                            nums.append(v)



        # -----------------------
        # tuple数据库格式
        # -----------------------

        elif isinstance(row,tuple):


            for x in row:

                if isinstance(x,int):

                    if 1<=x<=49:

                        nums.append(x)



    # ==========================
    # 防止空数据
    # ==========================


    if len(nums)==0:


        raise RuntimeError(

            "预测器没有获取到历史号码"

        )



    # ==========================
    # 频率模型
    # ==========================


    freq=Counter(nums)



    ranking=sorted(

        range(1,50),

        key=lambda x:

        freq.get(x,0),

        reverse=True

    )



    top10=ranking[:10]



    scores={}



    for n in top10:


        scores[str(n)] = round(

            freq.get(n,0)
            /
            max(freq.values()),

            3

        )



    return {


        "state":

        "NORMAL",


        "numbers":

        top10,


        "top3":

        top10[:3],


        "first":

        top10[0],


        "scores":

        scores,


        "attributes":{


            "说明":

            "V10融合预测"


        }


    }
