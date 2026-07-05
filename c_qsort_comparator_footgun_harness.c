
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>

int safe_relational_cmp(const void *a, const void *b) {
    int ia = *(const int*)a;
    int ib = *(const int*)b;
    if (ia < ib) return -1;
    if (ia > ib) return 1;
    return 0;
}
int safe_branchless_cmp(const void *a, const void *b) {
    int ia = *(const int*)a;
    int ib = *(const int*)b;
    return (ia > ib) - (ia < ib);
}

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "usage: case_json\n"); return 2; }
    FILE *f = fopen(argv[1], "r");
    if (!f) { perror("fopen"); return 2; }
    fseek(f, 0, SEEK_END);
    long sz = ftell(f); fseek(f, 0, SEEK_SET);
    char *buf = malloc(sz+1); fread(buf,1,sz,f); buf[sz]=0; fclose(f);
    
    // very crude json parse – we only need a few fields
    // expects: "synthetic_input":[...], "element_count":N, "comparator_label":"...", "operation_label":"...", "bsearch_key":K
    int arr[256]; int n=0;
    char *p = strstr(buf, "\"synthetic_input\"");
    if (p) {
        p = strchr(p, '[');
        if (p) { p++; while (*p && *p != ']' && n < 256) {
            while (*p==' '||*p==','||*p=='\n'||*p=='\r'||*p=='\t') p++;
            if (*p==']'|| *p==0) break;
            char *end; long v = strtol(p, &end, 10);
            if (end==p) break;
            arr[n++] = (int)v; p = end;
        }}
    }
    int element_count = n;
    p = strstr(buf, "\"element_count\"");
    if (p) { p = strchr(p, ':'); if(p) element_count = atoi(p+1); }
    
    char cmp_label[128] = "safe_int_relational";
    p = strstr(buf, "\"comparator_label\"");
    if (p) { p = strchr(p, ':'); if(p){ p = strchr(p, '"'); if(p){ p++; char *q=cmp_label; while(*p && *p!='"' && q-cmp_label<120) *q++ = *p++; *q=0; } } }
    
    char op_label[32] = "qsort";
    p = strstr(buf, "\"operation_label\"");
    if (p) { p = strchr(p, ':'); if(p){ p = strchr(p, '"'); if(p){ p++; char *q=op_label; while(*p && *p!='"' && q-op_label<30) *q++ = *p++; *q=0; } } }
    
    int bsearch_key = 0; int have_bkey = 0;
    p = strstr(buf, "\"bsearch_key\"");
    if (p) { p = strchr(p, ':'); if(p){ bsearch_key = atoi(p+1); have_bkey=1; } }
    
    int (*cmp)(const void*, const void*) = safe_relational_cmp;
    if (strstr(cmp_label, "branchless")) cmp = safe_branchless_cmp;
    
    if (strcmp(op_label, "bsearch")==0) {
        if (n>0) qsort(arr, n, sizeof(int), cmp);
        int *found = have_bkey ? (int*)bsearch(&bsearch_key, arr, n, sizeof(int), cmp) : NULL;
        printf("{\"c_harness_status\":\"ok\",\"operation\":\"bsearch\",\"n\":%d,\"found\":%s}\n", n, found?"true":"false");
        return 0;
    } else {
        if (n>0) qsort(arr, n, sizeof(int), cmp);
        printf("{\"c_harness_status\":\"ok\",\"operation\":\"qsort\",\"n\":%d,\"sorted\":[", n);
        for (int i=0;i<n;i++) printf("%s%d", i?",":"", arr[i]);
        printf("]}\n");
        return 0;
    }
}
