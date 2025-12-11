# Update Notes

This directory holds notes on the updater logic extracted from `ChituUpgrade.bin`. The OTA check lives in `ota_get_info_AIC` at address `0x93e94`, where the firmware assembles and calls 
`https://mms.chituiot.com/mainboardVersionUpdate/getInfo.do7` to see if a new package is available.

```bash
BASE_URL='https://mms.chituiot.com/mainboardVersionUpdate/getInfo.do7'
MACHINE_TYPE='ELEGOO Saturn 4 Ultra 16K'
MACHINE_ID='0'
VERSION='1.4.4'
LANG='en'
FIRMWARE_TYPE='1'

curl -sS --fail \
	--get "${BASE_URL}" \
	--data-urlencode "machineType=${MACHINE_TYPE}" \
	--data "machineId=${MACHINE_ID}" \
	--data "version=${VERSION}" \
	--data "lan=${LANG}" \
	--data "firmwareType=${FIRMWARE_TYPE}"
```

```json
{
	"success": true,
	"code": "000000",
	"messages": null,
	"data": {
		"update": true,
		"version": "01.05.00",
		"packageUrl": "https://download.chitubox.com/chitusystems/chitusystems/public/printer/firmware/release/1/c86accbdb98c4c9c8813a554b7561921/1/01.05.00/2025-12-02/680c20a74c154242a4556054d631aafb.zip",
		"firmwareType": 1,
		"packageHash": "c54e9dbbd34579767580d834255fe87a",
		"updateStrategy": 2,
		"log": "This firmware update enhances the APP-integrated axis control page navigation and residue detection notifications, and adds APP-based light toggle",
		"dataInfoId": "15cbfd42d9254bc9b7bef1288dc8aaaf"
	}
}
```

```bash
$ md5sum 680c20a74c154242a4556054d631aafb.zip
c54e9dbbd34579767580d834255fe87a  680c20a74c154242a4556054d631aafb.zip
```

```bash
$ unzip 680c20a74c154242a4556054d631aafb.zip
Archive:  680c20a74c154242a4556054d631aafb.zip
  inflating: ChituUpgrade.bin
```

```bash
$ head ChituUpgrade.bin
# <- this is for comment / total file size must be less than 4KB
#upgrade_bin_version=V1.5.0
#upgrade_force=1
```
