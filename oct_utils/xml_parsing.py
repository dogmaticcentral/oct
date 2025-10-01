import xml.etree.ElementTree as ET
from oct_utils.data_structures import PosteriorPoleData
from datetime import datetime


def get_date(tree, xmlfile, datepath) -> list[int] | None:
    ret_list = []
    for datepart in ["Year", "Month", "Day"]:
        entry  = tree.findall(f"{datepath}/{datepart}")
        if len(entry) != 1:
            print(f"Warning: expected exactly one {datepart} entry in {xmlfile}. No output written")
            return None
        entry = int(entry[0].text.strip())
        ret_list.append(entry)
    return ret_list


def fractional_years(start_date: list[int], end_date: list[int]) -> float:
    # Convert tuples to datetime objects
    (year, month, day) = start_date
    start = datetime(year, month, day)

    (year, month, day) = end_date
    end = datetime(year, month, day)

    # Calculate the difference
    difference = end - start

    # Calculate difference in years
    difference_in_years = (difference.days + difference.seconds / 86400) / 365.2425
    return round(difference_in_years, 1)


def calculate_age_at_test(tree: ET, xmlfile) -> float | None:
    # age at test
    patient_birthdate = get_date(tree, xmlfile, ".//Patient/Birthdate/Date")
    if patient_birthdate is None: return
    study_date = get_date(tree, xmlfile, ".//Patient/Study/StudyDate/Date")
    if study_date is None: return
    return fractional_years(patient_birthdate, study_date)


def find_laterality(tree, xmlfile, debug=False) -> str | None:
    laterality =  tree.findall(".//Series/Laterality")
    if len(laterality) != 1:
        print(f"Warning: expected exactly one laterality entry in {xmlfile}. No output written")
        return None
    laterality = laterality[0].text.strip().upper()
    if laterality not in ["R", "L"]:
        print(f"Warning: unexpected laterality value in {xmlfile}: '{laterality}'. No output written")
        return None
    laterality = "OD" if laterality == "R" else "OS"
    if debug: print(f"laterality: {laterality}")

    return laterality


def find_patient_name(tree, xmlfile, debug=False) -> str | None:
    last_name =  tree.findall(".//Patient/LastName")
    if len(last_name) != 1:
        print(f"Warning: expected exactly one last name entry in {xmlfile}. No output written")
        return None
    last_name = last_name[0].text.strip()

    first_names =  tree.findall(".//Patient/FirstNames")
    if len(first_names) != 1:
        print(f"Warning: expected exactly one first names entry in {xmlfile}. No output written")
        return None
    first_name = first_names[0].text.strip()

    name = f"{first_name} {last_name}"
    if debug: print(f"name: {name}")

    return name


def find_age_at_test(tree, xmlfile, debug=False) -> float | None:
    age_at_test =  tree.findall(".//Patient/AgeAtTest")
    if len(age_at_test) != 1:
        print(f"Warning: expected exactly one last age at test entry in {xmlfile}. No output written")
        return None
    age_at_test = age_at_test[0].text.strip()
    try:
        age_at_test = float(age_at_test)
    except Exception as e:
        print(f"Warning: expected float value as age at test in {xmlfile}: {e}. No output written")
        return None

    if debug: print(f"age at test: {age_at_test}")

    return age_at_test


def find_total_volume(tree, xmlfile, debug=False) -> float | None:
    # Note that this is actually coming form the bullseyegrid
    total_volume =  tree.findall(".//ThicknessGrid/TotalVolume")
    if len(total_volume) != 1:
        print(f"Warning: expected exactly one total volume in {xmlfile}. No output written")
        return None
    total_volume = total_volume[0].text.strip()
    try:
        total_volume = float(total_volume)
    except Exception as e:
        print(f"Warning: expected float value as age at test in {xmlfile}: {e}. No output written")
        return None

    if debug: print(f"age at test: {total_volume}")

    return total_volume


def extract_meta_data(tree: ET, xmlfile: str, debug=False) -> list[str] | None:

    laterality = find_laterality(tree, xmlfile)
    if laterality is None: return

    alias = find_patient_name(tree, xmlfile)
    if alias is None: return

    # age at test
    age_at_test = find_age_at_test(tree, xmlfile)
    if age_at_test is None:
        print(f"looking for birthdate and exam date")
        age_at_test = calculate_age_at_test(tree, xmlfile)
        if age_at_test is None:  return

    # total volume
    tot_vol = find_total_volume(tree, xmlfile)
    # we will not skip the rest if the total macular value according to Optos is not found

    return [laterality, alias, age_at_test, tot_vol]


def extract_pp_map(xmlfile, debug=False) -> PosteriorPoleData | None:

    tree = ET.parse(xmlfile)
    metadata = extract_meta_data(tree, xmlfile)
    if metadata is None: return None
    [laterality, alias, age_at_test, tot_vol] = metadata

    ppd = PosteriorPoleData()
    ppd.laterality = laterality
    ppd.alias = alias
    ppd.age_at_test  = age_at_test
    ppd.total_volume = tot_vol  # this might be None

    pp_grid_found = False
    for grid in tree.findall(".//ThicknessGrid"):
        grid_name = grid.find('Name').text
        if grid_name != "8x8 Posterior Pole Grid": continue
        if debug: print(grid_name)
        for zone in grid.findall("./Zone"):
            pp_grid_found = True
            zone_name = zone.find('Name').text
            zone_thck = zone.find('AvgThickness').text
            if zone_thck is None: continue
            zone_thck = float(zone_thck)

            zone_valid_pctg = float(zone.find('ValidPixelPercentage').text)

            row = int(zone_name[0]) - 1
            col = int(zone_name[2]) - 1
            if debug: print(f" {row} {col} {zone_name}  {zone_thck}  {zone_valid_pctg}")
            ppd.pp_map.loc[row, col]  = zone_thck
            ppd.weights.loc[row, col] = zone_valid_pctg

    if not pp_grid_found:
        print(f"Warning: no post pole grid found in {xmlfile}")
        return None

    return ppd

