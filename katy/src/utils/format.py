import json
class customDict(dict):

    def __str__(self) -> str:
        
        dict_items = super().items()
        final_string = "{ "
        for it in dict_items:
            str_to_add = f"{it[0]}: "
            if type(it[1]) == dict:
                rec_dict = customDict(it[1])
                str_to_add += rec_dict.__str__()
            elif type(it[1]) == list:
                str_to_add += json.dumps(it[1])
            else:
                str_to_add += str(it[1])
            final_string += str_to_add + ', '
            
        return final_string[0:-2] + ' }'