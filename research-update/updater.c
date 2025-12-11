/*
 * Reconstructed updater logic from ELF at address 0x93e94 (ota_get_info_AIC).
 * This is decompiled pseudocode to illustrate how the firmware checks for updates.
 */

#include <stddef.h>
#include <pthread.h>

// Forward declarations for external routines observed in the binary.
extern int log_async_output(const char *tag, int level, const char *fmt, ...);
extern int aic_get_online(int unused);
extern void *device_get_soc_id(void);
extern void utils_hex2str(const void *src, void *dst, size_t len_bytes);
extern const char *aic_get_version(void *buf);
extern void hl_convert_version_string_to_version2(const char *ver);
extern void ota_url_space_fill(const char *model, char *out, int out_len);
extern const char *language_str;              // language string table (offset indexed by dword_237EA0)
extern unsigned int dword_237EA0;             // current language index
extern int curl_slist_append(int list, const char *header);
extern int hl_curl_get2(const char *url, char *resp, int resp_sz, int timeout_s, int headers);
extern int cJSON_Parse(const char *text);
extern int cJSON_GetObjectItem(int obj, const char *key);
extern int cJSON_IsTrue(int obj);
extern double cJSON_GetNumberValue(int obj);
extern void cJSON_Delete(int obj);
extern int pthread_mutex_lock(void *m);
extern int pthread_mutex_unlock(void *m);
extern void pthread_exit(int status);
extern void *memset(void *s, int c, size_t n);
extern int sprintf(char *buf, const char *fmt, ...);
extern int printf(const char *fmt, ...);
extern void strncpy(char *dst, const char *src, size_t n);
extern void stime(const void *when);
extern void curl_slist_free_all(int list);

// Global state referenced by the updater.
extern int stru_1C4EA0;          // mutex
extern int ota_ctx;              // status context; high 32 bits used as state
extern unsigned char byte_1C58DB;   // flag: update available
extern char byte_1C58DC[0x100];     // new version string
extern char byte_1C59DC[0x100];     // package URL
extern char byte_1C5ADC[0x21];      // package hash
extern unsigned char byte_1C5AFD;   // update strategy
extern char byte_1C5AFE[0x800];     // update log

void ota_get_info_AIC(void) {
    char soc_hex[16];       // converted SOC ID
    char version_buf[0x100];
    char model[256];
    char resp[1500];
    char url[2048];
    char header[2052];
    int header_list;
    int json;

    log_async_output("ota", 4, "AIC get version start\n");
    if (!aic_get_online(0)) {
        pthread_mutex_lock(&stru_1C4EA0);
        byte_1C58DB = 0;
        ((int *)&ota_ctx)[1] = 2;  // set state = 2 (offline)
        pthread_mutex_unlock(&stru_1C4EA0);
        pthread_exit(0);
    }

    memset(resp, 0, sizeof(resp));
    memset(version_buf, 0, sizeof(version_buf));
    memset(model, 0, sizeof(model));
    memset(url, 0, sizeof(url));
    memset(header, 0, sizeof(header));

    // Build machineId from SOC ID
    *(long long *)soc_hex = (long long)device_get_soc_id();
    utils_hex2str(soc_hex, soc_hex, 8);
    memset(soc_hex, 0, sizeof(soc_hex));

    const char *ver = aic_get_version(NULL);
    hl_convert_version_string_to_version2(ver);

    // Fill model name with URL-safe encoding
    ota_url_space_fill("ELEGOO Saturn 4 Ultra 16K", model, sizeof(model));

    // Construct update query URL
    sprintf(
        url,
        "%s%s%s%s%s%s%s%s%s%d%s%s",
        "https://mms.chituiot.com/",
        "mainboardVersionUpdate/getInfo.do7",
        "?machineId=",
        soc_hex,
        "&version=",
        version_buf,
        "&lan=",
        &language_str[64 * (unsigned char)dword_237EA0],
        "&firmwareType=",
        2,
        "&machineType=",
        model);

    log_async_output("ota", 4, "curl url : %s\n", url);

    // Language header
    sprintf(header, "%s%s", "Accept-Language: ", &language_str[64 * (unsigned char)dword_237EA0]);
    log_async_output("ota", 4, "curl head : %s\n", header);
    header_list = curl_slist_append(0, header);

    if (hl_curl_get2(url, resp, sizeof(resp), 120, header_list)) {
        log_async_output("ota", 4, "curl get ota info failed\n");
        pthread_mutex_lock(&stru_1C4EA0);
        ((int *)&ota_ctx)[1] = 4;  // error
        pthread_mutex_unlock(&stru_1C4EA0);
    } else {
        printf("respone : %s\n", resp);
        json = cJSON_Parse(resp);
        if (json) {
            pthread_mutex_lock(&stru_1C4EA0);
            int success = cJSON_GetObjectItem(json, "success");
            int data = cJSON_GetObjectItem(json, "data");
            if (!success || !data || cJSON_IsTrue(success) != 1) {
                ((int *)&ota_ctx)[1] = 3;  // parse failure
            } else {
                int update = cJSON_GetObjectItem(data, "update");
                byte_1C58DB = cJSON_IsTrue(update) == 1;
                printf("update = %d\n", byte_1C58DB);
                if (byte_1C58DB) {
                    int ver_item = cJSON_GetObjectItem(data, "version");
                    strncpy(byte_1C58DC, *(const char **)(ver_item + 16), sizeof(byte_1C58DC));

                    int url_item = cJSON_GetObjectItem(data, "packageUrl");
                    strncpy(byte_1C59DC, *(const char **)(url_item + 16), sizeof(byte_1C59DC));

                    int hash_item = cJSON_GetObjectItem(data, "packageHash");
                    strncpy(byte_1C5ADC, *(const char **)(hash_item + 16), sizeof(byte_1C5ADC));

                    int strategy_item = cJSON_GetObjectItem(data, "updateStrategy");
                    byte_1C5AFD = (unsigned char)cJSON_GetNumberValue(strategy_item);

                    int log_item = cJSON_GetObjectItem(data, "log");
                    strncpy(byte_1C5AFE, *(const char **)(log_item + 16), sizeof(byte_1C5AFE));
                    printf("log:%s\n", byte_1C5AFE);

                    int time_item = cJSON_GetObjectItem(data, "timeMS");
                    double time_ms = cJSON_GetNumberValue(time_item);
                    long when = (long)(time_ms / 1000.0);
                    stime(&when);
                }
                ((int *)&ota_ctx)[1] = 2;  // success
            }
            pthread_mutex_unlock(&stru_1C4EA0);
        } else {
            log_async_output("ota", 2, "ota_get_info failed\n");
            pthread_mutex_lock(&stru_1C4EA0);
            ((int *)&ota_ctx)[1] = 3;
            pthread_mutex_unlock(&stru_1C4EA0);
        }
        cJSON_Delete(json);
    }

    curl_slist_free_all(header_list);
    log_async_output("ota", 4, "pthread exit\n");
    pthread_exit(0);
}
