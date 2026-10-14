"""Execute a clean source notebook into an ignored, local results notebook."""
import sys
import argparse
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from jupyter_client.kernelspec import KernelSpecManager


def main():
    root=Path(__file__).resolve().parents[1]
    parser=argparse.ArgumentParser()
    parser.add_argument('--notebook',default='01_player_metrics_exploration.ipynb')
    parser.add_argument('--in-process',action='store_true',help='Execute with local IPython when separate kernel startup is unavailable')
    args=parser.parse_args()
    if Path(args.notebook).name != args.notebook or not args.notebook.endswith('.ipynb'):
        raise ValueError('Use a notebook filename from the notebooks directory')
    source=root/'notebooks'/args.notebook
    notebook=nbformat.read(source,as_version=4)
    if args.in_process:
        import os
        from IPython.core.interactiveshell import InteractiveShell
        from IPython.utils.capture import capture_output
        from traitlets.config import Config
        os.chdir(root)
        config=Config()
        config.HistoryManager.hist_file=':memory:'
        shell=InteractiveShell.instance(config=config)
        count=0
        for cell in notebook.cells:
            if cell.cell_type!='code':
                continue
            count+=1
            with capture_output() as captured:
                result=shell.run_cell(cell.source,store_history=False)
            if result.error_before_exec or result.error_in_exec:
                raise RuntimeError(f'Notebook code cell {count} failed') from (result.error_before_exec or result.error_in_exec)
            cell.execution_count=count
            cell.outputs=[]
            for name,value in [('stdout',captured.stdout),('stderr',captured.stderr)]:
                if value:
                    cell.outputs.append(nbformat.v4.new_output('stream',name=name,text=value))
            for value in captured.outputs:
                cell.outputs.append(nbformat.v4.new_output('display_data',data=value.data,metadata=value.metadata))
        notebook.metadata['execution_method']='Local IPython in-process; separate kernel startup unavailable'
    else:
        manager=KernelSpecManager()
        spec=manager.get_kernel_spec('python3')
        # Use this interpreter, which has the validated local analysis dependencies.
        spec.argv[0]=sys.executable
        client=NotebookClient(notebook,timeout=180,kernel_name='python3',
            resources={'metadata':{'path':str(root)}},allow_errors=False)
        client.kernel_manager_class = __import__('jupyter_client').KernelManager
        client.create_kernel_manager()
        client.km.kernel_spec.argv[0]=sys.executable
        client.execute()
    output=root/'reports/exploration'/args.notebook.replace('.ipynb','.executed.ipynb')
    output.parent.mkdir(parents=True,exist_ok=True)
    nbformat.write(notebook,output)
    print(f'Executed {sum(c.cell_type=="code" for c in notebook.cells)} code cells without errors.')
    print(output)


if __name__=='__main__':main()
