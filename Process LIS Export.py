import csv, re


class EAP:
    def __init__(self):
        self.id = ''
        self.procedure_name = ''
        self.default_loinc_code = ''
        self.lab_test_record = ''
        self.lab_tests = []
        self.procedure_master = ''  # procedure code
        self.short_procedure_name = ''
        self.category = -1
        self.category_record_name = ''
        self.orderable = ''
        self.order_display_name = ''
        self.performable = ''
        self.synonyms = []

        # Location restrictions
        self._loc_restrict_list_op_record_name = []
        self._loc_restrict_list_ip_record_name = []
        self._sa_restrict_list_op_record_name = []
        self._sa_restrict_list_ip_record_name = []

    @property
    def loc_restrict_list_op_record_name(self):
        return self._loc_restrict_list_op_record_name

    @loc_restrict_list_op_record_name.setter
    def loc_restrict_list_op_record_name(self, value):
        self._loc_restrict_list_op_record_name = re.sub(r'[\r\n]+', ';', value)

    @property
    def loc_restrict_list_ip_record_name(self):
        return self._loc_restrict_list_ip_record_name

    @loc_restrict_list_ip_record_name.setter
    def loc_restrict_list_ip_record_name(self, value):
        self._loc_restrict_list_ip_record_name = re.sub(r'[\r\n]+', ';', value)

    @property
    def sa_restrict_list_op_record_name(self):
        return self._sa_restrict_list_op_record_name

    @sa_restrict_list_op_record_name.setter
    def sa_restrict_list_op_record_name(self, value):
        self._sa_restrict_list_op_record_name = re.sub(r'[\r\n]+', ';', value)

    @property
    def sa_restrict_list_ip_record_name(self):
        return self._sa_restrict_list_ip_record_name

    @sa_restrict_list_ip_record_name.setter
    def sa_restrict_list_ip_record_name(self, value):
        self._sa_restrict_list_ip_record_name = re.sub(r'[\r\n]+', ';', value)

    def __str__(self):
        return f'{self.id} {self.procedure_name} {self.lab_test_record} {self.lab_tests} {self.loc_restrict_list_op_record_name} {self.loc_restrict_list_ip_record_name}'

    def outpatient_location(self):
        return self.orderable_location('loc_restrict_list_op_record_name', 'loc_list_includes_op',
                                       'sa_restrict_list_op_record_name', 'sa_list_includes_op')

    def inpatient_location(self):
            return self.orderable_location('loc_restrict_list_ip_record_name', 'loc_list_includes_ip',
                                           'sa_restrict_list_ip_record_name', 'sa_list_includes_ip')

    def orderable_location(self, location_attr, location_includes_attr, sa_attr, sa_includes_attr):
        # If this is set to Yes, only the included locations will be allowed to order. If it is set to No, the listed
        # locations will not be able to order.
        locations = getattr(self, location_attr).lower()
        service_areas = getattr(self, sa_attr).lower()

        include_listed_locations = False
        if 'yes' in getattr(self, location_includes_attr).lower():
            include_listed_locations = True

        if include_listed_locations and 'bch oak main hospital' in locations:
            return 'EB'
        if not include_listed_locations and 'bch oak main hospital' in locations:
            return 'WB'

        include_listed_service_areas = False
        if 'yes' in getattr(self, sa_includes_attr).lower():
            include_listed_service_areas = True

        if include_listed_service_areas and 'marin health outpatient practices service area' in \
                service_areas and len(service_areas.split(';')) == 2:
            return 'Marin'

        if locations.strip() == '':
            return 'EB / WB'
        print(f'Unknown location: {getattr(self, location_includes_attr).lower()} {locations} \n {getattr(self, sa_includes_attr).lower()} {service_areas}')
        return '??'

    def performing_labs(self):
        labs = []
        for test in self.lab_tests:
            labs.append(test.acc_lab_2_record_name)
        return ';'.join(labs)


class OVT:
    def __init__(self):
        self.id = ''

    def __str__(self):
        return f'{self.id} {self.name} {self.synonyms}'


def extract_information(table, file_name, fields, dict_to_store, header_count=4):
    with open(file_name, encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')

        for i in range(0, header_count):
            next(reader)

        # Get the index of each field in the header
        header = next(reader)
        header_text = [name.lower() for name in header]
        for field_name, value in fields.items():
            header_index = header_text.index(field_name)
            fields[field_name]['index'] = header_index

        for row in reader:
            if table == 'EAP':
                # Look for "Beaker EAP", not sure if this is 100% accurate way to do it
                if "BEAKER EAP" not in row[239].upper() or "HISTOTRAC EAP" in row[239].upper():
                    continue

                if "UCSF CASE CONVERSION" in row[806].upper():
                    continue

            # Go through each field and set the attribute to the value in the cell
            id_index = fields['id #']['index']
            id = row[id_index].strip()
            new_obj = table_to_object[table]()
            dict_to_store[id] = new_obj
            for field_name, value in fields.items():
                setattr(new_obj, value['attribute'], row[value['index']].strip())


# The key is the name of the column (lower case), and the attribute is what the property will be called once it is added
# to the OVT object
ovt_fields = {
    'id #': {'attribute': 'id', 'index': -1},
    'name': {'attribute': 'name', 'index': -1},
    'synonyms': {'attribute': 'synonyms', 'index': -1},
    'components': {'attribute': 'components', 'index': -1},
    'components record name': {'attribute': 'components_record_name', 'index': -1},
    'allowed methods': {'attribute': 'allowed_methods', 'index': -1},
    'allowed methods record name': {'attribute': 'allowed_methods_record_name', 'index': -1},
    'acc lab 2 record name': {'attribute': 'acc_lab_2_record_name', 'index': -1},
    'acc lab 1 record name': {'attribute': 'acc_lab_1_record_name', 'index': -1},
    'acc containers record name': {'attribute': 'acc_containers_record_name', 'index': -1},
    'acc sharing': {'attribute': 'acc_sharing', 'index': -1},
}

eap_fields = {
    'id #': {'attribute': 'id', 'index': -1},
    'procedure name': {'attribute': 'procedure_name', 'index': -1},
    'default loinc code': {'attribute': 'default_loinc_code', 'index': -1},
    'lab test record': {'attribute': 'lab_test_record', 'index': -1},
    'procedure master #': {'attribute': 'procedure_master', 'index': -1},
    'short procedure name': {'attribute': 'short_procedure_name', 'index': -1},
    'category': {'attribute': 'category', 'index': -1},
    'category record name': {'attribute': 'category_record_name', 'index': -1},
    'orderable': {'attribute': 'orderable', 'index': -1},
    'order display name': {'attribute': 'order_display_name', 'index': -1},
    'performable': {'attribute': 'performable', 'index': -1},
    'synonyms': {'attribute': 'synonyms', 'index': -1},
    'loc restrict list op record name': {'attribute': 'loc_restrict_list_op_record_name', 'index': -1},
    'loc list includes op': {'attribute': 'loc_list_includes_op', 'index': -1},
    'loc restrict list ip record name': {'attribute': 'loc_restrict_list_ip_record_name', 'index': -1},
    'loc list includes ip': {'attribute': 'loc_list_includes_ip', 'index': -1},
    'sa restrict list op record name': {'attribute': 'sa_restrict_list_op_record_name', 'index': -1},
    'sa list includes op': {'attribute': 'sa_list_includes_op', 'index': -1},
    'sa restrict list ip record name': {'attribute': 'sa_restrict_list_ip_record_name', 'index': -1},
    'sa list includes ip': {'attribute': 'sa_list_includes_ip', 'index': -1},
}

table_to_object = {
    'EAP': EAP,
    'OVT': OVT,
}

procedures = {}
tests = {}
extract_information('EAP', 'Procedure Data.csv', eap_fields, procedures)
extract_information('OVT', 'Test Data.csv', ovt_fields, tests)


# Adds test information to procedures
for procedure in procedures.values():
    lab_tests = re.split(r'[\r\n]+', procedure.lab_test_record)
    for test in lab_tests:
        try:
            procedure.lab_tests.append(tests[test])
        except Exception as e:
            print(f'Test {test} not found in tests dictionary')
            print(e)

with open('Test Info.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['ID', 'EAP', 'Procedure Name', 'Inpatient Ordering', 'Outpatient Ordering', 'Performing Labs'])
    for eap in procedures.values():
        writer.writerow([eap.id, eap.procedure_master, eap.procedure_name, eap.inpatient_location(), eap.outpatient_location(), eap.performing_labs()])
