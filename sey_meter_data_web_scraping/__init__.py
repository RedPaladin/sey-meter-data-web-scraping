''' Entry file '''

from .utils import SeyDataSaver, SeyWebScraper

def collect_meterdatavalues(username, password, electrical_contract_id, water_contract_id, subject_id, data_folder, dt):
    ''' Collect the meter data values '''

    scrapper = SeyWebScraper(data_folder)

    try:
        scrapper.login(username, password)

        data_electricity, data_water = scrapper.collect(electrical_contract_id, water_contract_id, subject_id, dt)
        scrapper.logout()

        saver = SeyDataSaver(data_folder, dt)

        saver.save(data_electricity, data_water)

        saver.save_sums()
    finally:
        scrapper.close()