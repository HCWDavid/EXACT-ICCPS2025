from train import main
config = {
    'batch_size': 128,
    'epochs':200,
    'fsl': False,
    'model': 'segmenter',
    'seed': 73054772,
}
main(config)

# config = {
#     'batch_size': 128,
#     'epochs':200,
#     'fsl': False,
#     'model': 'transformer',
#     'seed': 73054772,
# }
# main(config)

# config = {
#     'batch_size': 128,
#     'epochs':200,
#     'fsl': False,
#     'model': 'LSTM',
#     'seed': 73054772,
# }
# main(config)

# config = {
#     'batch_size': 128,
#     'epochs':200,
#     'fsl': False,
#     'model': 'CRNN',
#     'seed': 73054772,
# }
# main(config)

# config = {
#     'batch_size': 128,
#     'epochs':200,
#     'fsl': False,
#     'model': 'CCRNN',
#     'seed': 73054772,
# }
# main(config)

# config = {
#     'batch_size': 128,
#     'epochs':200,
#     'fsl': False,
#     'model': 'UNet',
#     'seed': 73054772,
# }
# main(config)