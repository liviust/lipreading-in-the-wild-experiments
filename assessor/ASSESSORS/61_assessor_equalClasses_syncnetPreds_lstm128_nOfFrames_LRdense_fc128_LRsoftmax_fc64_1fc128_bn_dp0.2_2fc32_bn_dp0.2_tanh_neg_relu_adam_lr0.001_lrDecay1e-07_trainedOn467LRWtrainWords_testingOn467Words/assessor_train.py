import glob
import os

from keras.utils import plot_model

from assessor_evaluation import *
from assessor_functions import *
from assessor_model import *
from assessor_train_params import *


def contrastive_loss(y_true, y_pred):
    '''Contrastive loss from Hadsell-et-al.'06
    http://yann.lecun.com/exdb/publis/pdf/hadsell-chopra-lecun-06.pdf
    '''
    margin = 1
    return K.mean(y_true * K.square(y_pred) +
                  (1 - y_true) * K.square(K.maximum(margin - y_pred, 0)))


######################################################
# DIR, PARAMS
######################################################

finetune = False
residual_finetune = False

this_assessor_model_name, this_assessor_save_dir = make_this_assessor_model_name_and_save_dir_name(experiment_number, equal_classes, use_CNN_LSTM,
                                                                                                   mouth_nn, trainable_syncnet, grayscale_images,
                                                                                                   conv_f_1, conv_f_2, conv_f_3, mouth_features_dim,
                                                                                                   use_head_pose, lstm_units_1, use_softmax, use_softmax_ratios,
                                                                                                   individual_dense, lr_dense_fc, lr_softmax_fc,
                                                                                                   last_fc, dense_fc_1, dropout_p1, dense_fc_2, dropout_p2,
                                                                                                   syncnet_lstm_preds_dim, contrastive, contrastive_dense_fc_1, contrastive_dropout_p1,
                                                                                                   use_tanh_not_sigmoid,
                                                                                                   optimizer_name, adam_lr=adam_lr, adam_lr_decay=adam_lr_decay,
                                                                                                   residual_part=residual_part, finetune=finetune,
                                                                                                   train_collect_type=train_collect_type, test_number_of_words=test_number_of_words)

# Make the dir if it doesn't exist
if not os.path.exists(this_assessor_save_dir):
    print("Making dir", this_assessor_save_dir)
    os.makedirs(this_assessor_save_dir)

# Copy assessor_model file into this_assessor_save_dir
os.system("cp assessor_model.py " + this_assessor_save_dir)
print("Copied assessor_model.py to", this_assessor_save_dir)

# Copy assessor_params file into this_assessor_save_dir
os.system("cp assessor_params.py " + this_assessor_save_dir)
print("Copied assessor_params.py to", this_assessor_save_dir)

# Copy assessor_functions file into this_assessor_save_dir
os.system("cp assessor_functions.py " + this_assessor_save_dir)
print("Copied assessor_functions.py to", this_assessor_save_dir)

# Copy assessor_train_params file into this_assessor_save_dir
os.system("cp assessor_train_params.py " + this_assessor_save_dir)
print("Copied assessor_train_params.py to", this_assessor_save_dir)

# Copy assessor_train file into this_assessor_save_dir
os.system("cp assessor_train.py " + this_assessor_save_dir)
print("Copied assessor_train.py to", this_assessor_save_dir)

######################################################
# MAKE MODEL
######################################################

assessor = my_assessor_model(use_CNN_LSTM=use_CNN_LSTM, use_head_pose=use_head_pose, mouth_nn=mouth_nn, trainable_syncnet=trainable_syncnet,
                             grayscale_images=grayscale_images, my_resnet_repetitions=my_resnet_repetitions,
                             conv_f_1=conv_f_1, conv_f_2=conv_f_2, conv_f_3=conv_f_3, mouth_features_dim=mouth_features_dim,
                             lstm_units_1=lstm_units_1, use_softmax=use_softmax, use_softmax_ratios=use_softmax_ratios,
                             individual_dense=individual_dense, lr_dense_fc=lr_dense_fc, lr_softmax_fc=lr_softmax_fc,
                             dense_fc_1=dense_fc_1, dropout_p1=dropout_p1, dense_fc_2=dense_fc_2, dropout_p2=dropout_p2, last_fc=last_fc,
                             residual_part=residual_part, res_fc_1=res_fc_1, res_fc_2=res_fc_2,
                             syncnet_lstm_preds_dim=syncnet_lstm_preds_dim, contrastive=contrastive, contrastive_dense_fc_1=contrastive_dense_fc_1, contrastive_dropout_p1=contrastive_dropout_p1,
                             use_tanh_not_sigmoid=use_tanh_not_sigmoid)

# for layer in assessor.layers:
#     if 'res' in layer.name:
#         layer.trainable = False

if loss == 'contrastive_loss':
    loss = contrastive_loss

assessor.compile(optimizer=optimizer, loss=loss, metrics=['accuracy'])

assessor.summary()

write_model_architecture(assessor, file_type='json', file_name=os.path.join(this_assessor_save_dir, this_assessor_model_name))
write_model_architecture(assessor, file_type='yaml', file_name=os.path.join(this_assessor_save_dir, this_assessor_model_name))

plot_model(assessor, to_file=os.path.join(this_assessor_save_dir, this_assessor_model_name+'.png'), show_shapes=True)

######################################################
# GEN BATCHES OF IMAGES
######################################################

train_data_generator = generate_assessor_data_batches(batch_size=batch_size, data_dir=data_dir, collect_type=train_collect_type, shuffle=shuffle, equal_classes=equal_classes,
                                                      use_CNN_LSTM=use_CNN_LSTM, mouth_nn=mouth_nn, grayscale_images=grayscale_images,
                                                      random_crop=random_crop, random_flip=random_crop, use_head_pose=use_head_pose,
                                                      use_softmax=use_softmax, use_softmax_ratios=use_softmax_ratios, verbose=verbose,
                                                      use_LRW_train=use_LRW_train, train_samples_per_word=train_samples_per_word,
                                                      test_number_of_words=test_number_of_words)

val_data_generator = generate_assessor_data_batches(batch_size=batch_size, data_dir=data_dir, collect_type=train_collect_type, shuffle=shuffle, equal_classes=equal_classes,
                                                      use_CNN_LSTM=use_CNN_LSTM, mouth_nn=mouth_nn, grayscale_images=grayscale_images,
                                                      random_crop=False, random_flip=False, use_head_pose=use_head_pose,
                                                      use_softmax=use_softmax, use_softmax_ratios=use_softmax_ratios, verbose=verbose,
                                                      use_LRW_train=use_LRW_train, train_samples_per_word=train_samples_per_word,
                                                      test_number_of_words=test_number_of_words)

######################################################
# CALLBACKS
######################################################

lr_reducer = ReduceLROnPlateau(factor=np.sqrt(0.1), patience=5, verbose=1)

early_stopper = EarlyStopping(min_delta=0.001, patience=20)

checkpointAndMakePlots = CheckpointAndMakePlots(file_name_pre=this_assessor_model_name, save_dir=this_assessor_save_dir)

######################################################
# TRAIN (Step 1 of PFT)
######################################################

# this_assessor_model_name = 'syncnet_lstm'
# this_assessor_save_dir = '/home/voletiv/GitHubRepos/lipreading-in-the-wild-experiments/assessor/ASSESSORS/SYNCNET_LSTM'
# mouth_nn = 'make_syncnet_lstm_only'
# syncnet_lstm_classify, syncnet_lstm = my_assessor_model(mouth_nn=mouth_nn, lstm_units_1=lstm_units_1)
# lrw_syncnet_preds_train = load_syncnet_preds(collect_type='train')
# lrw_lipreader_dense_train, lrw_lipreader_softmax_train, lrw_correct_one_hot_y_arg_train = load_dense_softmax_y(collect_type='train')
# lrw_syncnet_preds_val = load_syncnet_preds(collect_type='val')
# lrw_lipreader_dense_val, lrw_lipreader_softmax_val, lrw_correct_one_hot_y_arg_val = load_dense_softmax_y(collect_type='val')
# lrw_syncnet_preds_test = load_syncnet_preds(collect_type='test')
# lrw_lipreader_dense_test, lrw_lipreader_softmax_test, lrw_correct_one_hot_y_arg_test = load_dense_softmax_y(collect_type='test')
# train_inputs = np.vstack((lrw_syncnet_preds_train, lrw_syncnet_preds_val))
# train_outputs = np.zeros((len(train_inputs), 500))
# for i in range(len(lrw_correct_one_hot_y_arg_train)):
#     train_outputs[i][lrw_correct_one_hot_y_arg_train[i]] = 1

# for i in range((len(lrw_correct_one_hot_y_arg_val))):
#     train_outputs[len(lrw_correct_one_hot_y_arg_train) + i][lrw_correct_one_hot_y_arg_val[i]] = 1

# val_inputs = lrw_syncnet_preds_test
# val_outpus = np.zeros((len(lrw_syncnet_preds_test), 500))
# for i in range(len(lrw_correct_one_hot_y_arg_test)):
#     val_outpus[i][lrw_correct_one_hot_y_arg_test[i]] = 1

# syncnet_lstm_classify.compile(optimizer=optimizer, loss='categorical_crossentropy', metrics=['accuracy'])
# syncnet_lstm_classify.fit(x=train_inputs, y=train_outputs, batch_size=1000, epochs=100, verbose=1, callbacks=[lr_reducer, checkpointAndMakePlots], validation_data=[val_inputs, val_outpus], shuffle=True, class_weight=class_weight)

# LRW_train_syncnet_lstm_preds = syncnet_lstm.predict(lrw_syncnet_preds_train)
# LRW_val_syncnet_lstm_preds = syncnet_lstm.predict(lrw_syncnet_preds_val)
# LRW_test_syncnet_lstm_preds = syncnet_lstm.predict(lrw_syncnet_preds_test)

saved_final_model = False
initial_epoch = 0

try:
    assessor.fit_generator(train_data_generator,
                           steps_per_epoch=train_steps_per_epoch,
                           # steps_per_epoch=1,
                           epochs=n_epochs,
                           # callbacks=[lr_reducer, early_stopper, checkpointAndMakePlots],
                           callbacks=[lr_reducer, checkpointAndMakePlots],
                           # callbacks=[early_stopper, checkpointAndMakePlots],
                           # callbacks=[checkpointAndMakePlots],
                           validation_data=val_data_generator,
                           validation_steps=val_steps_per_epoch,
                           # validation_steps=1,
                           class_weight=class_weight,
                           initial_epoch=initial_epoch)
except KeyboardInterrupt:
    print("Saving latest weights as", os.path.join(this_assessor_save_dir, this_assessor_model_name+"_assessor.hdf5"), "...")
    assessor.save(os.path.join(this_assessor_save_dir, "assessor.hdf5"))
    print("Saving model as", os.path.join(this_assessor_save_dir, "assessor.hdf5"), "...")
    assessor.save("assessor.hdf5")
    print("Predicting...")
    # Predict val
    # eval_batch_size = 100
    # lrw_val_data_generator = generate_assessor_data_batches(batch_size=eval_batch_size, data_dir=data_dir, collect_type="val", shuffle=False, equal_classes=False,
    #                                                         use_CNN_LSTM=use_CNN_LSTM, mouth_nn=mouth_nn, use_head_pose=use_head_pose, use_softmax=use_softmax,
    #                                                         grayscale_images=grayscale_images, random_crop=False, random_flip=False, verbose=False,
    #                                                         use_LRW_train=use_LRW_train, train_samples_per_word=train_samples_per_word)
    # lrw_val_assessor_preds = np.array([])
    # for i in tqdm.tqdm(range(25000//eval_batch_size)):
    #     [X, y] = next(lrw_val_data_generator)
    #     lrw_val_assessor_preds = np.append(lrw_val_assessor_preds, assessor.predict(X))
    # Predict test
    eval_batch_size = 100
    lrw_test_data_generator = generate_assessor_data_batches(batch_size=batch_size, data_dir=data_dir, collect_type="test", shuffle=False, equal_classes=False,
                                                             use_CNN_LSTM=use_CNN_LSTM, mouth_nn=mouth_nn, grayscale_images=grayscale_images,
                                                             random_crop=False, random_flip=False, use_head_pose=use_head_pose,
                                                             use_softmax=use_softmax, use_softmax_ratios=use_softmax_ratios, verbose=False,
                                                             use_LRW_train=use_LRW_train, train_samples_per_word=train_samples_per_word,
                                                             test_number_of_words=test_number_of_words)
    lrw_test_assessor_preds = np.array([])
    for i in tqdm.tqdm(range(25000//eval_batch_size)):
        [X, y] = next(lrw_test_data_generator)
        lrw_test_assessor_preds = np.append(lrw_test_assessor_preds, assessor.predict(X))
    # Save preds
    np.savez(os.path.join(this_assessor_save_dir, "assessor_preds"), lrw_val_assessor_preds=lrw_val_assessor_preds, lrw_test_assessor_preds=lrw_test_assessor_preds)
    saved_final_model = True
    # EVALUATE
    evaluate_assessor(lrw_val_assessor_preds=lrw_val_assessor_preds, lrw_test_assessor_preds=lrw_test_assessor_preds, assessor='CNN',
                      assessor_save_dir=this_assessor_save_dir, assessor_threshold=0.5)

if not saved_final_model:
    print("Saving latest weights as", os.path.join(this_assessor_save_dir, this_assessor_model_name+"_assessor.hdf5"), "...")
    assessor.save(os.path.join(this_assessor_save_dir, "assessor.hdf5"))
    print("Saving model as", os.path.join(this_assessor_save_dir, "assessor.hdf5"), "...")
    assessor.save("assessor.hdf5")
    print("Predicting...")
    # Predict val
    eval_batch_size = 100
    lrw_val_data_generator = generate_assessor_data_batches(batch_size=eval_batch_size, data_dir=data_dir, collect_type="val", shuffle=False, equal_classes=False,
                                                            use_CNN_LSTM=use_CNN_LSTM, mouth_nn=mouth_nn, use_head_pose=use_head_pose, use_softmax=use_softmax,
                                                            grayscale_images=grayscale_images, random_crop=False, random_flip=False, verbose=False)
    lrw_val_assessor_preds = np.array([])
    for i in tqdm.tqdm(range(25000//eval_batch_size)):
        [X, y] = next(lrw_val_data_generator)
        lrw_val_assessor_preds = np.append(lrw_val_assessor_preds, assessor.predict(X))
    # Predict test
    eval_batch_size = 100
    lrw_test_data_generator = generate_assessor_data_batches(batch_size=eval_batch_size, data_dir=data_dir, collect_type="test", shuffle=False, equal_classes=False,
                                                             use_CNN_LSTM=use_CNN_LSTM, mouth_nn=mouth_nn, use_head_pose=use_head_pose, use_softmax=use_softmax,
                                                             grayscale_images=grayscale_images, random_crop=False, random_flip=False, verbose=False)
    lrw_test_assessor_preds = np.array([])
    for i in tqdm.tqdm(range(25000//eval_batch_size)):
        [X, y] = next(lrw_test_data_generator)
        lrw_test_assessor_preds = np.append(lrw_test_assessor_preds, assessor.predict(X))
    # Save preds
    np.savez("lrw_assessor_preds", lrw_val_assessor_preds, lrw_test_assessor_preds)
    evaluate_assessor(lrw_val_assessor_preds=lrw_val_assessor_preds, lrw_test_assessor_preds=lrw_test_assessor_preds, assessor='CNN',
                      assessor_save_dir=this_assessor_save_dir, assessor_threshold=0.5)

print("Done.")


######################################################
# RSIDUAL FINE-TUNE (Step 2 of PFT)
######################################################


if residual_finetune:

    # Load last best model
    assessor.load_weights(sorted(glob.glob(os.path.join(this_assessor_save_dir, "*_epoch*.hdf5")))[-2])

    for layer in assessor.layers:
        if 'res' in layer.name:
            layer.trainable = True
        else:
            layer.trainable = False

    # # Use very less learning rate
    # adam_lr = 1e-7
    # adam_lr_decay = 1e-3
    # optimizer = Adam(lr=adam_lr, beta_1=0.9, beta_2=0.999, epsilon=1e-08, decay=adam_lr_decay)
    optimizer_name = 'SGD_lr1e-05_decay1e-3'
    optimizer = SGD(lr=1e-5, momentum=0.5, decay=1e-3)
    assessor.compile(optimizer=optimizer, loss=loss, metrics=['accuracy'])

    this_assessor_model_name, this_assessor_save_dir = make_this_assessor_model_name_and_save_dir_name(experiment_number, equal_classes, use_CNN_LSTM,
                                                                                                       mouth_nn, trainable_syncnet, grayscale_images,
                                                                                                       conv_f_1, conv_f_2, conv_f_3, mouth_features_dim,
                                                                                                       use_head_pose, lstm_units_1, use_softmax, use_softmax_ratios,
                                                                                                       individual_dense, lr_dense_fc, lr_softmax_fc,
                                                                                                       last_fc, dense_fc_1, dropout_p1, dense_fc_2, dropout_p2,
                                                                                                       optimizer_name, adam_lr=adam_lr, adam_lr_decay=adam_lr_decay,
                                                                                                       finetune=True)

    # Make the dir if it doesn't exist
    if not os.path.exists(this_assessor_save_dir):
        print("Making dir", this_assessor_save_dir)
        os.makedirs(this_assessor_save_dir)

    # Copy assessor_model file into this_assessor_save_dir
    os.system("cp assessor_model.py " + this_assessor_save_dir)
    print("Copied assessor_model.py to", this_assessor_save_dir)

    # Copy assessor_train_params file into this_assessor_save_dir
    os.system("cp assessor_train_params.py " + this_assessor_save_dir)
    print("Copied assessor_train_params.py to", this_assessor_save_dir)

    # Copy assessor_train file into this_assessor_save_dir
    os.system("cp assessor_train.py " + this_assessor_save_dir)
    print("Copied assessor_train.py to", this_assessor_save_dir)

    # New
    train_data_generator = generate_assessor_data_batches(batch_size=batch_size, data_dir=data_dir, collect_type=train_collect_type, shuffle=shuffle, equal_classes=equal_classes,
                                                     use_CNN_LSTM=use_CNN_LSTM, mouth_nn=mouth_nn, use_head_pose=use_head_pose, use_softmax=use_softmax,
                                                     grayscale_images=grayscale_images, random_crop=random_crop, random_flip=random_flip, verbose=verbose)

    test_data_generator = generate_assessor_data_batches(batch_size=batch_size, data_dir=data_dir, collect_type=val_collect_type, shuffle=shuffle, equal_classes=equal_classes,
                                                   use_CNN_LSTM=use_CNN_LSTM, mouth_nn=mouth_nn, use_head_pose=use_head_pose, use_softmax=use_softmax,
                                                   grayscale_images=grayscale_images, random_crop=False, random_flip=False, verbose=verbose)

    lr_reducer = ReduceLROnPlateau(factor=np.sqrt(0.1), patience=5, min_lr=5e-7, verbose=1)
    checkpointAndMakePlots = CheckpointAndMakePlots(file_name_pre=this_assessor_model_name, this_assessor_save_dir=this_assessor_save_dir)

    saved_final_model = False

    try:
        assessor.fit_generator(train_data_generator,
                               steps_per_epoch=train_steps_per_epoch,
                               # steps_per_epoch=1,
                               epochs=n_epochs,
                               # callbacks=[lr_reducer, early_stopper, checkpointAndMakePlots],
                               callbacks=[lr_reducer, checkpointAndMakePlots],
                               # callbacks=[checkpointAndMakePlots],
                               validation_data=test_data_generator,
                               validation_steps=val_steps_per_epoch,
                               # validation_steps=1,
                               class_weight=class_weight,
                               initial_epoch=0)
    except KeyboardInterrupt:
        print("Saving latest weights as", os.path.join(this_assessor_save_dir, this_assessor_model_name+"_assessor.hdf5"), "...")
        assessor.save_weights(os.path.join(this_assessor_save_dir, this_assessor_model_name+"_assessor.hdf5"))
        saved_final_model = True

    if not saved_final_model:
        print("Saving latest weights as", os.path.join(this_assessor_save_dir, this_assessor_model_name+"_assessor.hdf5"), "...")
        assessor.save_weights(os.path.join(this_assessor_save_dir, this_assessor_model_name+"_assessor.hdf5"))
        saved_final_model = True

    print("Done.")



######################################################
# FINE-TUNE (Step 2 of PFT)
######################################################

if finetune:

    # Make syncnet trainable
    assessor.layers[3].layer.trainable = True

    # Load last best model
    assessor.load_weights(sorted(glob.glob(os.path.join(this_assessor_save_dir, "*_epoch*.hdf5")))[-2])

    # Use very less learning rate
    adam_lr = 1e-4
    adam_lr_decay = 1e-2
    optimizer = Adam(lr=adam_lr, beta_1=0.9, beta_2=0.999, epsilon=1e-08, decay=adam_lr_decay)

    assessor.compile(optimizer=optimizer, loss=loss, metrics=['accuracy'])

    this_assessor_model_name, this_assessor_save_dir = make_this_assessor_model_name_and_save_dir_name(experiment_number, equal_classes, use_CNN_LSTM,
                                                                                                       mouth_nn, trainable_syncnet, grayscale_images,
                                                                                                       conv_f_1, conv_f_2, conv_f_3, mouth_features_dim,
                                                                                                       use_head_pose, lstm_units_1, use_softmax, use_softmax_ratios,
                                                                                                       individual_dense, lr_dense_fc, lr_softmax_fc,
                                                                                                       last_fc, dense_fc_1, dropout_p1, dense_fc_2, dropout_p2,
                                                                                                       optimizer_name, adam_lr=adam_lr, adam_lr_decay=adam_lr_decay,
                                                                                                       finetune=True)

    # Make the dir if it doesn't exist
    if not os.path.exists(this_assessor_save_dir):
        print("Making dir", this_assessor_save_dir)
        os.makedirs(this_assessor_save_dir)

    # Copy assessor_model file into this_assessor_save_dir
    os.system("cp assessor_model.py " + this_assessor_save_dir)
    print("Copied assessor_model.py to", this_assessor_save_dir)

    # Copy assessor_train_params file into this_assessor_save_dir
    os.system("cp assessor_train_params.py " + this_assessor_save_dir)
    print("Copied assessor_train_params.py to", this_assessor_save_dir)

    # Copy assessor_train file into this_assessor_save_dir
    os.system("cp assessor_train.py " + this_assessor_save_dir)
    print("Copied assessor_train.py to", this_assessor_save_dir)

    batch_size = batch_size // 4

    train_lrw_word_set_num_txt_file_names = read_lrw_word_set_num_file_names(collect_type=train_collect_type, collect_by='sample')
    train_steps_per_epoch = len(train_lrw_word_set_num_txt_file_names) // batch_size // 8
    val_steps_per_epoch = train_steps_per_epoch

    # New
    train_data_generator = generate_assessor_data_batches(batch_size=batch_size, data_dir=data_dir, collect_type=train_collect_type, shuffle=shuffle, equal_classes=equal_classes,
                                                     use_CNN_LSTM=use_CNN_LSTM, mouth_nn=mouth_nn, use_head_pose=use_head_pose, use_softmax=use_softmax,
                                                     grayscale_images=grayscale_images, random_crop=random_crop, random_flip=random_flip, verbose=verbose)

    val_data_generator = generate_assessor_data_batches(batch_size=batch_size, data_dir=data_dir, collect_type=val_collect_type, shuffle=shuffle, equal_classes=equal_classes,
                                                   use_CNN_LSTM=use_CNN_LSTM, mouth_nn=mouth_nn, use_head_pose=use_head_pose, use_softmax=use_softmax,
                                                   grayscale_images=grayscale_images, random_crop=False, random_flip=False, verbose=verbose)

    checkpointAndMakePlots = CheckpointAndMakePlots(file_name_pre=this_assessor_model_name, this_assessor_save_dir=this_assessor_save_dir)

    saved_final_model = False

    try:
        assessor.fit_generator(train_data_generator,
                               steps_per_epoch=train_steps_per_epoch,
                               # steps_per_epoch=1,
                               epochs=n_epochs,
                               # callbacks=[lr_reducer, early_stopper, checkpointAndMakePlots],
                               callbacks=[checkpointAndMakePlots],
                               validation_data=val_data_generator,
                               validation_steps=val_steps_per_epoch,
                               # validation_steps=1,
                               class_weight=class_weight,
                               initial_epoch=0)
    except KeyboardInterrupt:
        print("Saving latest weights as", os.path.join(this_assessor_save_dir, this_assessor_model_name+"_assessor.hdf5"), "...")
        assessor.save_weights(os.path.join(this_assessor_save_dir, this_assessor_model_name+"_assessor.hdf5"))
        saved_final_model = True

    if not saved_final_model:
        print("Saving latest weights as", os.path.join(this_assessor_save_dir, this_assessor_model_name+"_assessor.hdf5"), "...")
        assessor.save_weights(os.path.join(this_assessor_save_dir, this_assessor_model_name+"_assessor.hdf5"))
        saved_final_model = True

    print("Done.")