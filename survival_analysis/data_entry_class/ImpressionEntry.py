import csv, pandas as pd


EMPTY = '<EMPTY>'
AMZBID_MAPPING_PATH = '..\PricePoints-3038-display.csv'
HEADER_BIDDING_KEYS = ('mnetbidprice',
                        'mnet_abd',
                        'mnet_fbcpm',
                        'amznbid',
                        'crt_pb',
                        'fb_bid_price_cents')

class ImpressionEntry:
    def __init__(self, doc):
        self.doc = doc
        self.load_amznbid_price_mapping()


    def build_entry(self):
        self.entry = {}

        self.entry['DeviceCategory'] = self.filter_empty_str(self.doc['DeviceCategory'])
        self.entry['MobileDevice'] = self.filter_empty_str(self.doc['MobileDevice'])
        self.entry['Browser'] = self.filter_empty_str(self.doc['Browser']).replace('Any.Any', '').strip()
        self.entry['BandWidth'] = self.filter_empty_str(self.doc['BandWidth'])
        self.entry['OS'] = self.filter_empty_str(self.doc['OS'])
        # self.entry['MobileCarrier'] = self.filter_empty_str(self.doc['MobileCarrier'])

        self.entry['Time'] = str(self.doc['Time'].hour)

        # self.entry['RequestLanguage'] = self.filter_empty_str(self.doc['RequestLanguage'])
        self.entry['Country'] = self.filter_empty_str(self.doc['Country'])
        self.entry['Region'] = self.filter_empty_str(self.doc['Region'])
        # self.entry['Metro'] = self.filter_empty_str(self.doc['Metro'])
        # self.entry['City'] = self.filter_empty_str(self.doc['City'])

        self.entry['RequestedAdUnitSizes'] = self.filter_empty_str(self.doc['RequestedAdUnitSizes']).split('|')
        self.entry['AdPosition'] = self.filter_empty_str(self.doc['AdPosition'])

        for k, v in self.parse_customtargeting(self.doc['CustomTargeting']).items():
            self.entry[k] = v


    def parse_customtargeting(self, ct):
        feat = {}

        feat['displaychannel'] = ct['displaychannel'] if 'displaychannel' in ct else EMPTY
        feat['displaysection'] = ct['displaysection'] if 'displaysection' in ct else EMPTY

        if 'channel' in ct:
            feat['channel'] = ct['channel'] if type(ct['channel']) == list else [ct['channel']]
        else:
            feat['channel'] = []

        if 'section' in ct:
            feat['section'] = ct['section'] if type(ct['section']) == list else [ct['section']]
        else:
            feat['section'] = []

        feat['trend'] = ct['trend'].lower() if 'trend' in ct else EMPTY
        # feat['src'] = ct['src'].lower() if 'src' in ct else EMPTY
        feat['type'] = ct['type'].lower() if 'type' in ct else EMPTY
        feat['ht'] = ct['ht'].lower() if 'ht' in ct else EMPTY

        # if max(self.get_headerbidding()) + 5 <= self.doc['SellerReservePrice']:
        #     print(self.doc['SellerReservePrice'], self.doc['CustomTargeting'])

        return feat

    def filter_empty_str(self, string):
        if not string or pd.isnull(string):
            return EMPTY
        return string.lower()

    def load_amznbid_price_mapping(self):
        self.amzbid_mapping = {}
        with open(AMZBID_MAPPING_PATH) as infile:
            csv_reader = csv.reader(infile, delimiter=',')
            next(csv_reader)
            for line in csv_reader:
                self.amzbid_mapping[line[-1]] = float(line[-2].replace('$', '').strip())

    def has_headerbidding(self):
        ct = self.doc['CustomTargeting']
        if any(hd in ct for hd in HEADER_BIDDING_KEYS if hd != 'amznbid') or ('amznbid' in ct and ct['amznbid'] in self.amzbid_mapping):
            return True
        return False

    def get_headerbids(self):
        ct = self.doc['CustomTargeting']
        header_bids = [None] * len(HEADER_BIDDING_KEYS)
        for i, hd_key in enumerate(HEADER_BIDDING_KEYS):
            if hd_key not in ct:
                continue

            if hd_key == 'fb_bid_price_cents':
                header_bids[i] = float(ct[hd_key]) / 100
            elif hd_key == 'amznbid':
                if ct[hd_key] in self.amzbid_mapping:
                    header_bids[i] = self.amzbid_mapping[ct[hd_key]]
            else:
                header_bids[i] = float(ct[hd_key])
        return header_bids

    def to_sparse_headerbids(self):
        sparse_rep = []
        for i, hd in enumerate(self.get_headerbids()):
            if hd is not None:
                sparse_rep.append(':'.join(map(str, [i, hd])))
        return sparse_rep

    def to_sparse_feature_vector(self, attr2idx):
        vector = []
        for attr, feats in self.entry.items():
            if type(feats) == list:
                for f in feats:
                    vector.append(':'.join(map(str, [attr2idx[attr][f], 1])))
            elif type(feats) == str:
                vector.append(':'.join(map(str, [attr2idx[attr][feats], 1])))
            else:
                vector.append(':'.join(map(str, [attr2idx[attr][attr], feats])))
        # append header bids
        # for i, bid in enumerate(self.get_headerbidding()):
        #     if bid == 0:
        #         continue
        #     vector.append(':'.join(map(str, [n_feats + i, bid])))
        return vector
