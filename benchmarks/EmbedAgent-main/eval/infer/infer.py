import json
from transformers import AutoTokenizer
import argparse
from prompt import translate_prompt, generate_prompt, example_connection, example_connection_answer
from untils import read_json, remove_annotation,gpt_response,add_retrieve_code
from untils import deepseek_base_url,deepseek_api_key,TOT_DATA
import json
from tqdm import tqdm
import os
import concurrent.futures

def process_single_example(i, examples, prompts, args):
    """处理单个示例的线程函数"""
    parameters = {
        'model': args.model_name,
        'max_tokens': args.max_tokens,
        'temperature': args.temperature,
        'stop': args.stop,
    }
        
    # 调用GPT接口
    response = gpt_response(
        prompts[i], 
        args.api_key, 
        args.base_url,
        parameters
    )
    print(response)
    print('----------------')
    # 更新结果（由于每个线程处理不同的i，这里不需要额外加锁）
    examples[i]['generation'] = response
    
    return i  # 返回索引用于跟踪进度

def gen_result(examples, args):
    prompts = [ex["prompt"] for ex in examples]
    
    # 创建线程池（可根据CPU核心数调整max_workers）
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        # 提交所有任务
        futures = [
            executor.submit(
                process_single_example,
                i, examples, prompts, args
            )
            for i in range(len(examples))
        ]
        
        # 使用tqdm显示进度条
        for _ in tqdm(
            concurrent.futures.as_completed(futures),
            total=len(futures),
            desc="Generating"
        ):
            pass  # 只需等待任务完成
    process_single_example(0, examples, prompts, args)
    
    return examples

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_name', type=str, default='deepseek-chat')
    parser.add_argument('--temperature', type=float, default=0)
    parser.add_argument('--max_tokens', type=int, default=8192)
    parser.add_argument('--stop', type=str, default='')
    parser.add_argument('--api_key', type=str, default=deepseek_api_key)
    parser.add_argument('--base_url', type=str, default=deepseek_base_url)
    parser.add_argument('--data_path', type=str, default='./dataset/prompt.jsonl')
    parser.add_argument('--task', type=str, default='translate_Pi-Pico_micro-python', help='with_connection, without_connection, translate_platform_lang')
    parser.add_argument('--platform', type=str, default='Arduino Mega')
    parser.add_argument('--total_data', type=int, default=TOT_DATA)
    parser.add_argument('--sample_indices', type=int, nargs='+', default=None, help='List of sample indices to use (default: all indices)')
    parser.add_argument('--output_dir', type=str, default='./dataset/infer_results')

    args = parser.parse_args()
    target_index = []
    if args.sample_indices is None:
        args.sample_indices = list(range(args.total_data))
    # create output dir
    os.makedirs(args.output_dir, exist_ok=True)
    cur_model_name = args.model_name.split("/")[-1]
    output_dir = f"{args.output_dir}/{cur_model_name}"
    os.makedirs(output_dir, exist_ok=True)
    if os.path.exists(f"{output_dir}/{args.task}.json"):
        ds = read_json(f"{output_dir}/{args.task}.json")
    else:
        ds = read_json(args.data_path)
    ds_compile = read_json("/mnt/ceph_home/xuruiyang2022/141nfs/code/iot/dataset/infer_results_raw/deepseek-reasoner/translate_ESP32_ESP-IDF_compile.jsonl")
    ds_res = read_json("/mnt/ceph_home/xuruiyang2022/141nfs/code/iot/dataset/infer_results_raw/deepseek-reasoner/translate_ESP32_ESP-IDF.json")
    # gen prompt
    prompts = []
    for index,sample in enumerate(ds):
        if index not in args.sample_indices: continue
        solution = remove_annotation(sample["sketch"],'c')
        problem = sample["problem"]
        diagram = sample["diagram"][args.platform]
        hardware_lst = sample["hardware_lst"]
        if args.task.startswith("translate"):
            task = {"platform": args.task.split("_")[1], "language": args.task.split("_")[2]}
            cur_prompt = translate_prompt(solution,diagram,hardware_lst,args.platform,task)
        else:
            cur_prompt = generate_prompt(problem,diagram,hardware_lst,args.task,args.platform)
        if args.platform == "Arduino Mega":
            cur_prompt = cur_prompt.replace("uno","mega")
        # cur_prompt = add_retrieve_code(cur_prompt,sample["hardware_lst"],['```arduino','```'])
        message = [
            {"role": "system", "content": "You are an expert in embeded system design."},
            {"role": "user", "content": cur_prompt}
        ]
        if ds_compile[index]["status"] == "Build failed!":
            target_index.append(index)
            message.append({"role": "assistant", "content": ds_res[index]["response"].split("</think>")[-1]})
            message.append({"role": "user", "content": f"""The code is build failed because of the following error:

                            
{ds_compile[index]['content']}


Please fix the error
Note:
1. Your connections should in [CONNECTIONS] and [/CONNECTIONS]
2. Your code should in [ESP32 Code] and [/ESP32 Code]
3. Even if the origin connection or code is correct, you should still rewrite it.
4. First give the connection and then give the code."""})
            prompts.append({"prompt":message})
    print(prompts[0]['prompt'][2]['content'])

    # gen result
    gen_res = gen_result(prompts,args)
    cnt = 0
    for index, sample_index in enumerate(target_index):
        ds_res[sample_index]["response"] = gen_res[index]['generation']
                    
    with open(f"{output_dir}/{args.task}.json","w",encoding="utf-8") as f:
        json.dump(ds_res,f,indent=4,ensure_ascii=False)