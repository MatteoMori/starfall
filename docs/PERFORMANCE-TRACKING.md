Performance tracking

PARAMETERS
    PARAMETER num_ctx 10000
    PARAMETER temperature 0.1
    PARAMETER top_p 0.1
    PARAMETER top_k 40

- qwen3:4b-instruct    --> A bit slow but GOOD results. Perfect answer
- qwen3:4b-q8_0        --> A bit slow as well ( 12GB Memory ) but results were missing the LATEST label
- qwen3:4b-instruct-2507-q4_K_M --> 





To try
 - Change context size: PARAMETER num_ctx 4096
   - qwen3:4b-instruct
   - qwen3:4b-q8_0
   - qwen3:4b-instruct-2507-q4_K_M