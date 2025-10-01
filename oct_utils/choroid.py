from statistics import mean

CHOROID_THICKNESS_CUTOFF = 440

def choroid_thckness(chorthck_df, alias, age, eye) -> float:

    alias = alias.replace("_", " ")
    cond1 = chorthck_df['Patient']==alias
    cond2 = abs(chorthck_df['Age at Visit'] - age) < 0.5
    # cond3 = chorthck_df['Eye']==eye
    conditions = cond1 & cond2
    filtered_df = chorthck_df[conditions]

    number_of_rows = len(filtered_df)
    if number_of_rows > 2:
        print(f"multiple thickness values found for {alias}  {eye}  {age}")
        exit()
    if number_of_rows == 1:
        thickness = filtered_df['JP Measurements (μm)'].iloc[0]
    elif number_of_rows == 2:  # I am assuming this is the left and the right eye
        thickness = mean(filtered_df['JP Measurements (μm)'].iloc[i] for i in range(2))
    else:
        # print(f"no thickness found for {alias} {age}, either eye")
        thickness =  -1.0

    return thickness


def choroid_thickness_normal(chorthck_df, alias, age, eye) -> bool:
    # the cutoff value of 440 is based on https://iovs.arvojournals.org/article.aspx?articleid=2127819
    # where they measure normal thickness in children age 10015 to be 359 ± 77 μm
    thickness =  choroid_thckness(chorthck_df, alias, age, eye)

    if thickness < CHOROID_THICKNESS_CUTOFF:
        return True
    else:
        # print(f"skipping {alias}  {eye}  {age}; choroidal thickness: {thickness/1000:.3f} mm")
        return False
