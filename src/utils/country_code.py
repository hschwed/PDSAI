import pycountry as pc

def get_iso2(code):
    """
    Takes ISO3 code of country and gets ICO2 code
    """
    country = pc.countries.get(alpha_3=code)
    return country.alpha_2 if country else None

def get_iso3(code):
    """
    Takes ISO2 code of country and gets ISO3 code
    """
    country = pc.countries.get(alpha_2=code)
    return country.alpha_3 if country else None

#print(iso2_to_iso3("AF"))
#print(iso3_to_iso2("AFG"))

def get_name(code):
    """
    Takes ISO3 code of country and gets name
    """
    return pc.countries.get(alpha_3=code).name